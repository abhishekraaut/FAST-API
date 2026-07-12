from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    currency: str = "INR"


class OrganizationOut(BaseModel):
    id: int
    name: str
    slug: str
    currency: str
