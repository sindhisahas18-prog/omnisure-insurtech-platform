"""
Idempotent seed script for Phase 1 reference data.

Run with:  python -m app.seed
"""

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.insurance_type import INSURANCE_TYPE_SEED, InsuranceType
from app.models.service_plan import SERVICE_PLAN_SEED, ServicePlan
from app.models.user import User, UserRole


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for row in INSURANCE_TYPE_SEED:
            if not db.query(InsuranceType).filter_by(code=row["code"]).first():
                db.add(InsuranceType(**row))

        for row in SERVICE_PLAN_SEED:
            if not db.query(ServicePlan).filter_by(code=row["code"]).first():
                db.add(ServicePlan(**row))

        if not db.query(User).filter_by(email="admin@omnisure.in").first():
            db.add(
                User(
                    full_name="OmniSure Admin",
                    email="admin@omnisure.in",
                    hashed_password=hash_password("ChangeMe123!"),
                    role=UserRole.admin,
                )
            )

        db.commit()
        print("Seed complete: insurance types, service plans, and demo admin user ready.")
        print("Demo admin login -> email: admin@omnisure.in / password: ChangeMe123!  (change this in production)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
