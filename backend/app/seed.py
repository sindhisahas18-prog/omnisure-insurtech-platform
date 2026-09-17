"""
Idempotent seed script for Phase 1 reference data.

Run with:  python -m app.seed
"""

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.claim_config import ClaimConfig
from app.models.insurance_type import INSURANCE_TYPE_SEED, InsuranceType
from app.models.service_plan import SERVICE_PLAN_SEED, ServicePlan
from app.models.user import User, UserRole
from app.services.claim_config_seed import CLAIM_CONFIG_SEED


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for row in INSURANCE_TYPE_SEED:
            if not db.query(InsuranceType).filter_by(code=row["code"]).first():
                db.add(InsuranceType(**row))
        db.commit()

        for row in SERVICE_PLAN_SEED:
            if not db.query(ServicePlan).filter_by(code=row["code"]).first():
                db.add(ServicePlan(**row))

        for type_code, config in CLAIM_CONFIG_SEED.items():
            insurance_type = db.query(InsuranceType).filter_by(code=type_code).first()
            if not insurance_type:
                continue
            if not db.query(ClaimConfig).filter_by(insurance_type_id=insurance_type.id).first():
                db.add(
                    ClaimConfig(
                        insurance_type_id=insurance_type.id,
                        incident_types=config["incident_types"],
                        damaged_components=config["damaged_components"],
                        required_documents=config["required_documents"],
                        dynamic_questions=config["dynamic_questions"],
                    )
                )

        if not db.query(User).filter_by(email="admin@omnisure.in").first():
            db.add(
                User(
                    full_name="OmniSure Admin",
                    email="admin@omnisure.in",
                    hashed_password=hash_password("ChangeMe123!"),
                    role=UserRole.admin,
                )
            )

        if not db.query(User).filter_by(email="reviewer@omnisure.in").first():
            db.add(
                User(
                    full_name="OmniSure Claims Reviewer",
                    email="reviewer@omnisure.in",
                    hashed_password=hash_password("ChangeMe123!"),
                    role=UserRole.employee,
                )
            )

        db.commit()
        print("Seed complete: insurance types, service plans, claim configs, and demo accounts ready.")
        print("Demo admin login    -> admin@omnisure.in    / ChangeMe123!")
        print("Demo employee login -> reviewer@omnisure.in / ChangeMe123!")
        print("(change these passwords before any real deployment)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
