import uuid

from pydantic import BaseModel


class InsuranceTypeOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    icon: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ServicePlanOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    price_inr: int
    is_most_popular: bool
    features: list[str]

    class Config:
        from_attributes = True
