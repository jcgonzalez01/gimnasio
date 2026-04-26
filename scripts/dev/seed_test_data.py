import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio actual al path para poder importar la app
sys.path.append(os.path.abspath("backend"))

from app.core.database import SessionLocal, engine
from app.models.member import Member, MemberMembership, MembershipPlan, MemberStatus

def seed_test_memberships():
    db = SessionLocal()
    try:
        # 1. Asegurarse de que haya planes
        plans = db.query(MembershipPlan).all()
        if not plans:
            print("No se encontraron planes. Creando planes por defecto...")
            plans = [
                MembershipPlan(name="Mensual", duration_days=30, price=500.00, color="#2196F3"),
                MembershipPlan(name="Anual", duration_days=365, price=4500.00, color="#9C27B0"),
            ]
            db.add_all(plans)
            db.commit()
            plans = db.query(MembershipPlan).all()
        
        plan_mensual = next((p for p in plans if p.name == "Mensual"), plans[0])
        plan_anual = next((p for p in plans if "Anual" in p.name), plans[0])

        # 2. Crear miembros de prueba si no existen
        test_members_data = [
            {
                "member_number": "T001",
                "first_name": "Juan",
                "last_name": "Pérez Test",
                "email": "juan.perez@example.com",
                "plan": plan_mensual
            },
            {
                "member_number": "T002",
                "first_name": "María",
                "last_name": "García Test",
                "email": "maria.garcia@example.com",
                "plan": plan_anual
            }
        ]

        for data in test_members_data:
            member = db.query(Member).filter(Member.member_number == data["member_number"]).first()
            if not member:
                print(f"Creando miembro: {data['first_name']} {data['last_name']}")
                member = Member(
                    member_number=data["member_number"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    email=data["email"],
                    status=MemberStatus.ACTIVE
                )
                db.add(member)
                db.flush() # Para obtener el ID

                # Asignar membresía activa
                start_date = datetime.utcnow()
                end_date = start_date + timedelta(days=data["plan"].duration_days)
                
                membership = MemberMembership(
                    member_id=member.id,
                    plan_id=data["plan"].id,
                    start_date=start_date,
                    end_date=end_date,
                    price_paid=data["plan"].price,
                    is_active=True
                )
                db.add(membership)
                print(f"Membresía '{data['plan'].name}' asignada a {data['first_name']}")
            else:
                print(f"El miembro {data['member_number']} ya existe.")

        db.commit()
        print("¡Proceso de creación de membresías de prueba completado!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_memberships()
