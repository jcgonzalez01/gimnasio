"""Notificaciones automáticas (vencimiento de membresías).

Usa APScheduler en background. Se inicia desde main.py si EMAIL_NOTIFICATIONS_ENABLED=true.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.member import Member, MemberMembership, MembershipPlan
from .email import send_email

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


# ── Plantillas ────────────────────────────────────────────────────────────────

def _expiry_email_html(member: Member, days_left: int, end_date: datetime) -> str:
    end_str = end_date.strftime("%d/%m/%Y")
    if days_left <= 0:
        title = "Tu membresía venció"
        msg = f"Tu membresía venció el <strong>{end_str}</strong>. Renueva para mantener tu acceso al gimnasio."
        color = "#DC2626"
    elif days_left == 1:
        title = "Tu membresía vence mañana"
        msg = f"Tu membresía vence el <strong>{end_str}</strong>. Te quedan <strong>1 día</strong>."
        color = "#F59E0B"
    else:
        title = f"Tu membresía vence en {days_left} días"
        msg = f"Tu membresía vence el <strong>{end_str}</strong>. Te quedan <strong>{days_left} días</strong>."
        color = "#F59E0B"

    return f"""
    <html><body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #2563EB, #1E40AF); color: white; padding: 24px; border-radius: 12px 12px 0 0;">
        <h1 style="margin: 0;">🏋️ GymSystem Pro</h1>
      </div>
      <div style="border: 1px solid #E5E7EB; border-top: none; padding: 24px; border-radius: 0 0 12px 12px;">
        <h2 style="color: {color}; margin-top: 0;">{title}</h2>
        <p>Hola <strong>{member.full_name}</strong>,</p>
        <p>{msg}</p>
        <p>Acércate a recepción para renovar tu plan o consulta los planes disponibles.</p>
        <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 24px 0;">
        <p style="color: #6B7280; font-size: 12px;">
          Este es un mensaje automático. Si ya renovaste, ignora este correo.
        </p>
      </div>
    </body></html>
    """


# ── Tareas ────────────────────────────────────────────────────────────────────

def check_expiring_memberships() -> dict:
    """Revisa membresías próximas a vencer y envía emails. Retorna stats."""
    sent = 0
    skipped = 0
    db = SessionLocal()
    try:
        days_thresholds = settings.expiry_reminder_days_list  # ej. [7,3,1]
        now = datetime.utcnow()

        for days in days_thresholds:
            target_start = now + timedelta(days=days)
            target_end = target_start + timedelta(days=1)

            memberships = db.query(MemberMembership).filter(
                MemberMembership.is_active == True,
                MemberMembership.end_date >= target_start,
                MemberMembership.end_date < target_end,
            ).all()

            for mem in memberships:
                member = mem.member
                if not member or not member.email:
                    skipped += 1
                    continue
                html = _expiry_email_html(member, days, mem.end_date)
                ok = send_email(
                    to=member.email,
                    subject=f"⏰ Tu membresía vence en {days} día{'s' if days != 1 else ''}",
                    html=html,
                )
                if ok:
                    sent += 1
                else:
                    skipped += 1

        # Membresías ya vencidas hoy (alerta única)
        expired = db.query(MemberMembership).filter(
            MemberMembership.is_active == True,
            MemberMembership.end_date >= now - timedelta(days=1),
            MemberMembership.end_date < now,
        ).all()
        for mem in expired:
            member = mem.member
            if not member or not member.email:
                continue
            html = _expiry_email_html(member, 0, mem.end_date)
            ok = send_email(
                to=member.email,
                subject="❌ Tu membresía venció",
                html=html,
            )
            if ok:
                sent += 1
            else:
                skipped += 1

        logger.info(f"Notificaciones de vencimiento: {sent} enviados, {skipped} omitidos.")
        return {"sent": sent, "skipped": skipped}
    finally:
        db.close()


def update_expired_member_status() -> dict:
    """Marca como 'expired' a miembros con todas sus membresías vencidas."""
    db = SessionLocal()
    updated = 0
    try:
        now = datetime.utcnow()
        members = db.query(Member).filter(Member.status == "active").all()
        for m in members:
            has_active = any(
                mem.is_active and mem.start_date <= now and mem.end_date >= now
                for mem in m.memberships
            )
            if not has_active and m.memberships:
                m.status = "expired"
                updated += 1
        db.commit()
        return {"updated": updated}
    finally:
        db.close()


# ── Scheduler ─────────────────────────────────────────────────────────────────

def start_scheduler() -> None:
    """Arranca el scheduler. Llamar una sola vez en startup."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")

    # Diario a las 09:00 UTC: revisar vencimientos
    _scheduler.add_job(
        check_expiring_memberships,
        CronTrigger(hour=9, minute=0),
        id="expiry_check",
        replace_existing=True,
    )

    # Diario a las 00:30 UTC: actualizar estados
    _scheduler.add_job(
        update_expired_member_status,
        CronTrigger(hour=0, minute=30),
        id="expire_status_update",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler de notificaciones iniciado.")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
