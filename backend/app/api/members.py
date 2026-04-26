from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, timedelta
import os, shutil, uuid, logging, threading

from ..core.database import get_db
from ..core.config import settings
from ..core.security import require_roles, get_current_user
from ..models.user import User
from ..models.member import Member, MembershipPlan, MemberMembership
from ..models.pos import Sale, SaleItem
from ..models.access import HikvisionDevice
from ..schemas.member import (
    MemberCreate, MemberUpdate, MemberOut, MemberListOut,
    MembershipPlanCreate, MembershipPlanUpdate, MembershipPlanOut,
    MemberMembershipCreate, MemberMembershipOut,
    AssignMembershipResponse, AccessEnrollResult,
)
from ..services.hikvision import HikvisionISAPI, image_file_to_base64
from ..services.audit import log_action
from ..services.deletion import assess_member, assess_plan, to_409_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/members", tags=["Miembros"])


def generate_member_number(db: Session) -> str:
    last = db.query(Member).order_by(Member.id.desc()).first()
    next_id = (last.id + 1) if last else 1
    return f"GYM{next_id:05d}"


# ── Planes de membresía ───────────────────────────────────────────────────────

@router.get("/plans", response_model=List[MembershipPlanOut])
def list_plans(db: Session = Depends(get_db)):
    return db.query(MembershipPlan).filter(MembershipPlan.is_active == True).all()


@router.post("/plans", response_model=MembershipPlanOut, status_code=201,
             dependencies=[Depends(require_roles("manager"))])
def create_plan(plan: MembershipPlanCreate, db: Session = Depends(get_db)):
    db_plan = MembershipPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.put("/plans/{plan_id}", response_model=MembershipPlanOut,
            dependencies=[Depends(require_roles("manager"))])
def update_plan(plan_id: int, plan: MembershipPlanUpdate, db: Session = Depends(get_db)):
    db_plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    for k, v in plan.model_dump(exclude_none=True).items():
        setattr(db_plan, k, v)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.delete("/plans/{plan_id}", dependencies=[Depends(require_roles("manager"))])
def delete_plan(plan_id: int,
                request: Request,
                force: bool = False,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    db_plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    impact = assess_plan(db, db_plan)
    if impact["history"] and not force:
        raise HTTPException(status_code=409,
                            detail=to_409_payload("El plan", impact))

    db_plan.is_active = False
    db.commit()
    log_action(db, user, "delete", entity_type="plan", entity_id=plan_id,
               summary=f"Desactivó plan '{db_plan.name}'" + (" (forzado)" if force else ""),
               request=request)
    return {"message": "Plan desactivado"}


# ── Miembros ──────────────────────────────────────────────────────────────────

@router.get("", response_model=List[MemberListOut])
def list_members(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(Member)
    if search:
        q = q.filter(or_(
            Member.first_name.ilike(f"%{search}%"),
            Member.last_name.ilike(f"%{search}%"),
            Member.email.ilike(f"%{search}%"),
            Member.phone.ilike(f"%{search}%"),
            Member.member_number.ilike(f"%{search}%"),
        ))
    if status:
        q = q.filter(Member.status == status)
    members = q.offset(skip).limit(limit).all()

    now = datetime.utcnow()
    result = []
    for m in members:
        active_mem = None
        for mem in m.memberships:
            if mem.start_date <= now and mem.end_date >= now and mem.is_active:
                active_mem = mem
                break
        result.append(MemberListOut(
            id=m.id,
            member_number=m.member_number,
            first_name=m.first_name,
            last_name=m.last_name,
            email=m.email,
            phone=m.phone,
            status=m.status,
            face_enrolled=m.face_enrolled,
            photo_path=m.photo_path,
            created_at=m.created_at,
            has_active_membership=active_mem is not None,
            membership_expires=active_mem.end_date if active_mem else None,
        ))
    return result


@router.post("", response_model=MemberOut, status_code=201)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    data = member.model_dump()
    # Convertir strings vacíos a None para campos con restricción UNIQUE
    for field in ("email", "phone"):
        if data.get(field) == "":
            data[field] = None

    db_member = Member(**data)
    db_member.member_number = generate_member_number(db)
    db.add(db_member)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        detail = str(exc.orig).lower()
        if "email" in detail:
            raise HTTPException(status_code=409,
                                detail="Ya existe un miembro con ese correo electrónico")
        if "phone" in detail:
            raise HTTPException(status_code=409,
                                detail="Ya existe un miembro con ese número de teléfono")
        raise HTTPException(status_code=409, detail="Dato duplicado — verifica email o teléfono")

    db.refresh(db_member)

    # ── Registrar en Hikvision en segundo plano (no bloquea si el dispositivo no responde) ──
    member_id  = db_member.id
    member_no  = db_member.hikvision_card_no
    full_name  = db_member.full_name

    def _bg_register():
        from ..core.database import SessionLocal
        bg_db = SessionLocal()
        try:
            m = bg_db.query(Member).filter(Member.id == member_id).first()
            if m:
                _register_member_on_devices(m, bg_db)
        finally:
            bg_db.close()

    threading.Thread(target=_bg_register, daemon=True).start()

    return db_member


def _register_member_on_devices(member: Member, db: Session,
                                 begin_time: Optional[str] = None,
                                 end_time: Optional[str] = None,
                                 enable_access: bool = False) -> List[dict]:
    """
    Registra/actualiza al miembro en todos los dispositivos Hikvision activos.
    enable_access=False → usuario registrado con acceso DESHABILITADO (enabled=false).
      ⚠️ NO usar fechas expiradas para bloquear: algunos dispositivos Hikvision
         rechazan PUT Modify para usuarios con fechas en el pasado, lo que impide
         la posterior actualización de fechas al asignar membresía.
    Retorna lista de resultados por dispositivo.
    """
    devices = db.query(HikvisionDevice).filter(
        HikvisionDevice.is_active == True,
        HikvisionDevice.device_type == "access_control",
    ).all()

    results = []
    for device in devices:
        try:
            hik = HikvisionISAPI(
                device.ip_address, device.port,
                device.username, device.password,
            )
            ok = hik.add_user(
                employee_no=str(member.id),
                name=member.full_name,
                begin_time=begin_time or "2020-01-01T00:00:00",
                end_time=end_time     or "2030-12-31T23:59:59",
                enabled=enable_access,   # False = sin acceso hasta asignar membresía
            )
            results.append({"device": device.name, "registered": ok})
            print(f"[HIK register_member] {member.full_name} (#{member.id}) "
                  f"→ {device.name}: {'OK' if ok else 'FAIL'}", flush=True)
        except Exception as exc:
            logger.error(f"Hikvision register error {device.name}: {exc}")
            results.append({"device": device.name, "registered": False, "error": str(exc)})

    # Guardar el ID de Hikvision en el perfil si aún no tiene
    if results and not member.hikvision_card_no:
        member.hikvision_card_no = str(member.id)
        db.commit()

    return results


@router.get("/{member_id}", response_model=MemberOut)
def get_member(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    return m


@router.put("/{member_id}", response_model=MemberOut)
def update_member(member_id: int, member: MemberUpdate, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    data = member.model_dump(exclude_none=True)
    # Convertir strings vacíos a None para campos únicos
    for field in ("email", "phone"):
        if data.get(field) == "":
            data[field] = None
    for k, v in data.items():
        setattr(db_member, k, v)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        detail = str(exc.orig).lower()
        if "email" in detail:
            raise HTTPException(status_code=409,
                                detail="Ya existe un miembro con ese correo electrónico")
        raise HTTPException(status_code=409, detail="Dato duplicado — verifica email o teléfono")
    db.refresh(db_member)
    return db_member


@router.delete("/{member_id}", dependencies=[Depends(require_roles("manager"))])
def delete_member(member_id: int,
                  request: Request,
                  force: bool = False,
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    impact = assess_member(db, m)
    if impact["blocked"]:
        raise HTTPException(status_code=409, detail=impact["block_reason"])
    if impact["history"] and not force:
        raise HTTPException(status_code=409,
                            detail=to_409_payload("El miembro", impact))

    # Eliminar del dispositivo Hikvision (en background, no bloquear si falla)
    member_id_val = m.id
    def _remove_from_devices():
        from ..core.database import SessionLocal
        from ..services.hikvision import HikvisionISAPI
        bg = SessionLocal()
        try:
            devs = bg.query(HikvisionDevice).filter(HikvisionDevice.is_active == True).all()
            for dev in devs:
                try:
                    hik = HikvisionISAPI(dev.ip_address, dev.port, dev.username, dev.password)
                    hik.delete_face(str(member_id_val))
                    hik.delete_user(str(member_id_val))
                except Exception:
                    pass
        finally:
            bg.close()
    threading.Thread(target=_remove_from_devices, daemon=True).start()

    # Borrado físico en la base de datos
    db.delete(m)
    db.commit()
    log_action(db, user, "delete", entity_type="member", entity_id=member_id_val,
               summary=f"Eliminó miembro '{m.full_name}'", request=request)
    return {"message": "Miembro eliminado"}


@router.patch("/{member_id}/face-status")
def update_face_status(member_id: int, face_enrolled: bool,
                       db: Session = Depends(get_db)):
    """
    Permite marcar/desmarcar manualmente el estado de enrolamiento facial.
    Útil para corregir falsos positivos cuando el dispositivo devolvió 200
    pero no almacenó la foto.
    """
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    m.face_enrolled = face_enrolled
    db.commit()
    return {"member_id": member_id, "face_enrolled": m.face_enrolled}


@router.post("/{member_id}/photo")
async def upload_photo(member_id: int, file: UploadFile = File(...),
                       db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes JPG/PNG")

    filename = f"member_{member_id}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.FACES_DIR, filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if m.photo_path and os.path.exists(m.photo_path):
        os.remove(m.photo_path)

    m.photo_path = f"/uploads/faces/{filename}"
    db.commit()
    return {"photo_path": m.photo_path}


# ── Membresías de miembro ─────────────────────────────────────────────────────

def _next_sale_number(db: Session) -> str:
    last = db.query(Sale).order_by(Sale.id.desc()).first()
    next_id = (last.id + 1) if last else 1
    return f"V{datetime.utcnow().strftime('%Y%m%d')}-{next_id:04d}"


@router.post("/{member_id}/memberships", response_model=AssignMembershipResponse, status_code=201)
def assign_membership(member_id: int, data: MemberMembershipCreate,
                      db: Session = Depends(get_db)):
    # ── Validaciones ──────────────────────────────────────────────────────────
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    plan = db.query(MembershipPlan).filter(MembershipPlan.id == data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    # ── Desactivar membresías anteriores ──────────────────────────────────────
    for prev in m.memberships:
        if prev.is_active:
            prev.is_active = False

    # ── Crear membresía ───────────────────────────────────────────────────────
    mem = MemberMembership(
        member_id=member_id,
        plan_id=data.plan_id,
        start_date=data.start_date,
        end_date=data.end_date,
        price_paid=data.price_paid,
        payment_method=data.payment_method,
        notes=data.notes,
    )
    db.add(mem)
    m.status = "active"

    # ── Generar venta POS ─────────────────────────────────────────────────────
    sale = Sale(
        sale_number=_next_sale_number(db),
        member_id=member_id,
        cashier="Sistema",
        subtotal=data.price_paid,
        discount=0.0,
        tax=0.0,
        total=data.price_paid,
        payment_method=data.payment_method,
        notes=f"Membresía: {plan.name} "
              f"({data.start_date.strftime('%d/%m/%Y')} – {data.end_date.strftime('%d/%m/%Y')})",
        status="completed",
    )
    db.add(sale)
    db.flush()  # obtener sale.id antes del commit

    sale_item = SaleItem(
        sale_id=sale.id,
        product_name=f"Membresía {plan.name}",
        quantity=1,
        unit_price=data.price_paid,
        discount=0.0,
        total=data.price_paid,
    )
    db.add(sale_item)

    mem.sale_id = sale.id
    db.commit()
    db.refresh(mem)
    db.refresh(sale)

    # ── Activar acceso Hikvision ──────────────────────────────────────────────
    access_results: List[AccessEnrollResult] = []
    access_enrolled = False
    access_skipped = False

    if not m.photo_path:
        access_skipped = True
    else:
        devices = db.query(HikvisionDevice).filter(
            HikvisionDevice.is_active == True,
            HikvisionDevice.device_type == "access_control",
        ).all()

        if not devices:
            access_skipped = True
        else:
            photo_fs = "." + m.photo_path
            begin_time = data.start_date.strftime("%Y-%m-%dT%H:%M:%S")
            end_time   = data.end_date.strftime("%Y-%m-%dT%H:%M:%S")

            try:
                import base64 as _b64, io as _io
                with open(photo_fs, "rb") as _f:
                    _raw = _f.read()
                # Convertir a JPEG si no lo es (Hikvision requiere JPEG)
                if not (_raw[:2] == b'\xff\xd8'):
                    from PIL import Image
                    _img = Image.open(_io.BytesIO(_raw)).convert("RGB")
                    _buf = _io.BytesIO()
                    _img.save(_buf, format="JPEG", quality=90)
                    _raw = _buf.getvalue()
                face_b64 = _b64.b64encode(_raw).decode("utf-8")
            except FileNotFoundError:
                face_b64 = None
                access_skipped = True
            except Exception as _ex:
                logger.error(f"Error convirtiendo foto a JPEG: {_ex}")
                face_b64 = None
                access_skipped = True

            if face_b64:
                for device in devices:
                    try:
                        hik = HikvisionISAPI(
                            device.ip_address, device.port,
                            device.username, device.password,
                        )
                        # Al asignar membresía → acceso habilitado con fechas reales
                        user_ok = hik.add_user(
                            employee_no=str(m.id),
                            name=m.full_name,
                            begin_time=begin_time,
                            end_time=end_time,
                            enabled=True,
                        )
                        face_res = hik.enroll_face(
                            employee_no=str(m.id),
                            face_image_b64=face_b64,
                            face_lib_id=device.face_lib_id,
                        )
                        ok = face_res.get("success", False)
                        access_results.append(AccessEnrollResult(
                            device=device.name,
                            user_added=user_ok,
                            face_enrolled=ok,
                            error=face_res.get("error") if not ok else None,
                        ))
                        if ok:
                            access_enrolled = True
                    except Exception as exc:
                        logger.error(f"Hikvision enroll error on {device.name}: {exc}")
                        access_results.append(AccessEnrollResult(
                            device=device.name,
                            user_added=False,
                            face_enrolled=False,
                            error=str(exc),
                        ))

                # Solo marcar face_enrolled si la FOTO fue aceptada por un endpoint
                # específico de cara (no solo porque el usuario fue registrado)
                if access_enrolled:
                    m.face_enrolled = True
                if any(r.user_added for r in access_results) and not m.hikvision_card_no:
                    m.hikvision_card_no = str(m.id)
                db.commit()

    return AssignMembershipResponse(
        membership=mem,
        sale_id=sale.id,
        sale_number=sale.sale_number,
        sale_total=sale.total,
        payment_method=data.payment_method,
        access_enrolled=access_enrolled,
        access_results=access_results,
        access_skipped=access_skipped,
    )


@router.get("/{member_id}/memberships", response_model=List[MemberMembershipOut])
def get_memberships(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    return m.memberships


# ── Actualizar vigencia en dispositivos Hikvision ──────────────────────────

@router.post("/{member_id}/update-validity")
def update_member_validity(
    member_id: int,
    begin_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    device_ids: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Actualiza las fechas de vigencia del acceso en los dispositivos Hikvision.
    NO modifica la membresía en la base de datos - solo sincroniza con los dispositivos.
    """
    from datetime import datetime as dt

    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    # Determinar fechas a usar
    if begin_date and end_date:
        bt = begin_date.strftime("%Y-%m-%dT%H:%M:%S")
        et = end_date.strftime("%Y-%m-%dT23:59:59")
    else:
        now = dt.utcnow()
        for mem in m.memberships:
            if mem.is_active and mem.start_date <= now and mem.end_date >= now:
                bt = mem.start_date.strftime("%Y-%m-%dT%H:%M:%S")
                et = mem.end_date.strftime("%Y-%m-%dT23:59:59")
                break
        else:
            raise HTTPException(
                status_code=400,
                detail="El miembro no tiene membresía activa. Asigna una primero.",
            )

    # Obtener dispositivos
    q = db.query(HikvisionDevice).filter(
        HikvisionDevice.is_active == True,
        HikvisionDevice.device_type == "access_control",
    )
    if device_ids:
        ids = [int(x) for x in device_ids.split(",") if x.strip().isdigit()]
        q = q.filter(HikvisionDevice.id.in_(ids))
    devices = q.all()

    if not devices:
        raise HTTPException(status_code=400, detail="No hay dispositivos activos")

    results = []
    all_ok = True
    for device in devices:
        try:
            hik = HikvisionISAPI(
                device.ip_address,
                device.port,
                device.username,
                device.password,
            )
            ok = hik.add_user(
                employee_no=str(m.id),
                name=m.full_name,
                begin_time=bt,
                end_time=et,
                enabled=True,
            )
            results.append({"device": device.name, "updated": ok})
            if not ok:
                all_ok = False
        except Exception as exc:
            logger.error(f"Error actualizando validez en {device.name}: {exc}")
            results.append({"device": device.name, "updated": False, "error": str(exc)})
            all_ok = False

    return {"success": all_ok, "results": results}


@router.delete("/del-membership/{membership_id}", dependencies=[Depends(require_roles("manager", "admin"))])
def delete_membership(membership_id: int,
                      request: Request,
                      user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """Elimina una membresía y actualiza el estado del miembro si no le quedan membresías activas."""
    mem = db.query(MemberMembership).filter(MemberMembership.id == membership_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")

    member_id = mem.member_id
    member_name = mem.member.full_name if mem.member else f"ID {member_id}"
    plan_name = mem.plan.name if mem.plan else "Desconocido"

    db.delete(mem)
    db.commit()

    # Si al miembro no le quedan membresías activas, marcar como expirado
    m = db.query(Member).filter(Member.id == member_id).first()
    if m:
        now = datetime.utcnow()
        active = any(om.is_active and om.start_date <= now <= om.end_date for om in m.memberships)
        if not active:
            m.status = "expired"
            db.commit()

    log_action(db, user, "delete_membership", entity_type="membership", entity_id=membership_id,
               summary=f"Eliminó membresía '{plan_name}' de {member_name}", request=request)
    
    return {"message": "Membresía eliminada correctamente"}
