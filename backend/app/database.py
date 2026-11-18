from collections.abc import Generator

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, with_loader_criteria

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


@event.listens_for(Session, "do_orm_execute")
def scope_demo_records(execute_state):
    """Keep public sample rows out of the owner's view and vice versa."""
    if not execute_state.is_select:
        return
    from app.models.activity import ActivityLog
    from app.models.admin import Admin
    from app.models.emi import EmiSchedule
    from app.models.loan import Loan
    from app.models.organization import Organization
    from app.models.payment import Payment

    demo = execute_state.session.info.get("demo_mode", False)
    if demo:
        org_filter = Organization.code.like("DEMO-ORG-%")
        loan_filter = Loan.loan_number.like("DEMO-LN-%")
        payment_filter = Payment.payment_number.like("DEMO-PAY-%")
        activity_filter = ActivityLog.admin_id.in_(
            select(Admin.id).where(Admin.username == "demo-viewer")
        )
    else:
        org_filter = Organization.code.not_like("DEMO-ORG-%")
        loan_filter = Loan.loan_number.not_like("DEMO-LN-%")
        payment_filter = Payment.payment_number.not_like("DEMO-PAY-%")
        activity_filter = ActivityLog.admin_id.not_in(
            select(Admin.id).where(Admin.username == "demo-viewer")
        )
    statement = execute_state.statement.options(
        with_loader_criteria(Organization, org_filter, include_aliases=True),
        with_loader_criteria(Loan, loan_filter, include_aliases=True),
        with_loader_criteria(Payment, payment_filter, include_aliases=True),
        with_loader_criteria(ActivityLog, activity_filter, include_aliases=True),
        with_loader_criteria(
            EmiSchedule,
            EmiSchedule.loan_id.in_(select(Loan.id).where(loan_filter)),
            include_aliases=True,
        ),
    )
    execute_state.statement = statement


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
