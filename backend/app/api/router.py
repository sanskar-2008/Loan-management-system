from fastapi import APIRouter

from app.api import activity, auth, dashboard, emis, loans, organizations, payments, reports, settings

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(loans.router)
api_router.include_router(emis.router)
# Route and table names stay `payments` for backward compatibility; UI copy displays this as "Repayment".
api_router.include_router(payments.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(settings.router)
api_router.include_router(activity.router)
