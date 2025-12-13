from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PredictionInput(BaseModel):
    """Input data for credit card approval prediction"""

    # Customer identification
    ID: int = Field(..., description="Customer ID")

    # Demographics
    CODE_GENDER: str = Field(..., description="Gender (M/F)")
    FLAG_OWN_CAR: str = Field(..., description="Owns car (Y/N)")
    FLAG_OWN_REALTY: str = Field(..., description="Owns realty (Y/N)")
    CNT_CHILDREN: int = Field(..., ge=0, description="Number of children")

    # Income
    AMT_INCOME_TOTAL: float = Field(..., gt=0, description="Total income")
    NAME_INCOME_TYPE: str = Field(..., description="Income type")

    # Education & Employment
    NAME_EDUCATION_TYPE: str = Field(..., description="Education level")
    NAME_FAMILY_STATUS: str = Field(..., description="Marital status")
    NAME_HOUSING_TYPE: str = Field(..., description="Housing type")
    OCCUPATION_TYPE: str = Field(..., description="Occupation")

    # Age & Employment
    DAYS_BIRTH: int = Field(..., description="Days since birth (negative)")
    DAYS_EMPLOYED: int = Field(..., description="Days employed (negative)")

    # Contact
    FLAG_MOBIL: int = Field(..., ge=0, le=1, description="Has mobile")
    FLAG_WORK_PHONE: int = Field(..., ge=0, le=1, description="Has work phone")
    FLAG_PHONE: int = Field(..., ge=0, le=1, description="Has phone")
    FLAG_EMAIL: int = Field(..., ge=0, le=1, description="Has email")

    # Family
    CNT_FAM_MEMBERS: float = Field(..., gt=0, description="Family members")

    class Config:
        json_schema_extra = {
            "example": {
                "ID": 5008804,
                "CODE_GENDER": "M",
                "FLAG_OWN_CAR": "Y",
                "FLAG_OWN_REALTY": "Y",
                "CNT_CHILDREN": 0,
                "AMT_INCOME_TOTAL": 180000.0,
                "NAME_INCOME_TYPE": "Working",
                "NAME_EDUCATION_TYPE": "Higher education",
                "NAME_FAMILY_STATUS": "Married",
                "NAME_HOUSING_TYPE": "House / apartment",
                "DAYS_BIRTH": -14000,
                "DAYS_EMPLOYED": -2500,
                "FLAG_MOBIL": 1,
                "FLAG_WORK_PHONE": 0,
                "FLAG_PHONE": 1,
                "FLAG_EMAIL": 0,
                "OCCUPATION_TYPE": "Managers",
                "CNT_FAM_MEMBERS": 2.0,
            }
        }


class PredictionOutput(BaseModel):
    """Output from prediction"""

    prediction: int = Field(..., description="0=Rejected, 1=Approved")
    probability: float = Field(..., ge=0, le=1, description="Approval probability")
    decision: str = Field(..., description="APPROVED or REJECTED")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    version: Optional[str] = Field(None, description="Model version used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 1,
                "probability": 0.85,
                "decision": "APPROVED",
                "confidence": 0.85,
                "version": "1",
                "timestamp": "2025-12-13T11:30:00",
            }
        }
