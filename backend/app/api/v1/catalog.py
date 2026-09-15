from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.insurance_type import InsuranceType
from app.models.service_plan import ServicePlan
from app.schemas.catalog import InsuranceTypeOut, ServicePlanOut

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


@router.get("/insurance-types", response_model=list[InsuranceTypeOut])
def list_insurance_types(db: Session = Depends(get_db)):
    return db.query(InsuranceType).filter(InsuranceType.is_active.is_(True)).order_by(InsuranceType.name).all()


@router.get("/service-plans", response_model=list[ServicePlanOut])
def list_service_plans(db: Session = Depends(get_db)):
    return db.query(ServicePlan).order_by(ServicePlan.price_inr).all()
