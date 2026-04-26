import sys
import os

# Añadir el directorio actual al path para poder importar la app
sys.path.append(os.path.abspath("backend"))

from app.core.database import SessionLocal
from app.models.member import MembershipPlan

def seed_extra_plans():
    db = SessionLocal()
    try:
        new_plans = [
            {
                "name": "Plan VIP Black",
                "description": "Acceso total, toallas incluidas y zona spa",
                "duration_days": 365,
                "price": 6000.0,
                "color": "#000000"
            },
            {
                "name": "Pase Fin de Semana",
                "description": "Válido viernes, sábado y domingo",
                "duration_days": 3,
                "price": 150.0,
                "color": "#E91E63"
            },
            {
                "name": "Plan Corporativo",
                "description": "Precio especial para empresas (mínimo 5 personas)",
                "duration_days": 30,
                "price": 400.0,
                "color": "#00BCD4"
            }
        ]

        for plan_data in new_plans:
            exists = db.query(MembershipPlan).filter(MembershipPlan.name == plan_data["name"]).first()
            if not exists:
                print(f"Creando plan: {plan_data['name']}")
                plan = MembershipPlan(**plan_data)
                db.add(plan)
            else:
                print(f"El plan {plan_data['name']} ya existe.")

        db.commit()
        print("¡Planes de membresía adicionales creados!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_extra_plans()
