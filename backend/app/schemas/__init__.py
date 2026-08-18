from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str


class AdminOut(BaseModel):
    id: str
    username: str
    email: str
    full_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None
    default_flat_rate: Decimal | None = Field(default=None, ge=0, le=100)
    default_compound_rate: Decimal | None = Field(default=None, ge=0, le=100)


class OrganizationUpdate(OrganizationCreate):
    status: Literal["active", "inactive"] | None = None


class OrganizationOut(BaseModel):
    id: str
    code: str
    name: str
    contact_phone: str | None
    contact_email: str | None
    notes: str | None
    default_flat_rate: Decimal | None
    default_compound_rate: Decimal | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationSummary(BaseModel):
    active_loans: int
    total_loans: int
    outstanding_balance: Decimal
    total_paid: Decimal
    principal_taken: Decimal


class LoanCreate(BaseModel):
    organization_id: str | None = None
    organization_name: str | None = Field(default=None, min_length=2, max_length=150)
    loan_type: Literal["flat", "compound"]
    principal_amount: Decimal = Field(gt=0)
    annual_interest_rate: Decimal = Field(ge=0, le=100)
    tenure_months: int = Field(ge=1, le=360)
    disbursement_date: date
    notes: str | None = None


class LoanPreviewRequest(BaseModel):
    loan_type: Literal["flat", "compound"]
    principal_amount: Decimal = Field(gt=0)
    annual_interest_rate: Decimal = Field(ge=0, le=100)
    tenure_months: int = Field(ge=1, le=360)
    disbursement_date: date


class EmiOut(BaseModel):
    id: str
    loan_id: str
    installment_no: int
    due_date: date
    principal_component: Decimal
    interest_component: Decimal
    total_due: Decimal
    amount_paid: Decimal
    status: str
    paid_at: datetime | None

    model_config = {"from_attributes": True}


class LoanOut(BaseModel):
    id: str
    loan_number: str
    organization_id: str
    borrower_id: str | None = None
    loan_type: str
    principal_amount: Decimal
    annual_interest_rate: Decimal
    tenure_months: int
    disbursement_date: date
    emi_amount: Decimal
    total_interest: Decimal
    total_payable: Decimal
    total_paid: Decimal
    total_interest_paid: Decimal
    outstanding_balance: Decimal
    status: str
    notes: str | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    organization_name: str | None = None
    organization_code: str | None = None

    model_config = {"from_attributes": True}


class LoanNotesUpdate(BaseModel):
    notes: str | None = None


class LoanStatusUpdate(BaseModel):
    status: Literal["defaulted", "cancelled"]


class PaymentCreate(BaseModel):
    loan_id: str
    amount: Decimal = Field(gt=0)
    payment_date: date
    payment_mode: Literal["cash", "upi", "bank_transfer", "cheque", "other"]
    reference_no: str | None = None
    notes: str | None = None
    emi_schedule_id: str | None = None


class PaymentVoidRequest(BaseModel):
    reason: str = Field(min_length=5)


class AllocationOut(BaseModel):
    id: str
    payment_id: str
    emi_schedule_id: str
    amount: Decimal
    principal_portion: Decimal
    interest_portion: Decimal

    model_config = {"from_attributes": True}


class PaymentOut(BaseModel):
    id: str
    payment_number: str
    loan_id: str
    amount: Decimal
    payment_date: date
    payment_mode: str
    reference_no: str | None
    notes: str | None
    is_voided: bool
    voided_at: datetime | None
    void_reason: str | None
    created_at: datetime
    loan_number: str | None = None

    model_config = {"from_attributes": True}


class SettingsOut(BaseModel):
    id: int
    company_name: str
    company_address: str | None
    company_phone: str | None
    logo_url: str | None
    currency_code: str
    currency_symbol: str
    default_flat_rate: Decimal
    default_compound_rate: Decimal
    late_fee_enabled: bool
    late_fee_type: str | None
    late_fee_value: Decimal
    overdue_alert_threshold_count: int | None

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    company_name: str | None = None
    company_address: str | None = None
    company_phone: str | None = None
    logo_url: str | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    currency_symbol: str | None = None
    default_flat_rate: Decimal | None = Field(default=None, ge=0)
    default_compound_rate: Decimal | None = Field(default=None, ge=0)
    late_fee_enabled: bool | None = None
    late_fee_type: str | None = None
    late_fee_value: Decimal | None = Field(default=None, ge=0)
    overdue_alert_threshold_count: int | None = None


class ActivityOut(BaseModel):
    id: str
    action: str
    entity_type: str | None
    entity_id: str | None
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StatusUpdate(BaseModel):
    status: Literal["active", "inactive"]
