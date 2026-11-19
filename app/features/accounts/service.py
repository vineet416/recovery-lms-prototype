from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import DISPOSITIONS, FINAL_STATUSES, STATUSES
from app.features.accounts.visibility import accounts_visible_to
from app.features.promises.service import mark_broken_ptps
from app.models import Account, AllocationHistory, CallLog, Office, Payment, Ptp, User

PAGE_SIZE = 50


# Turns the page text from the URL into a number; anything bad becomes 1.
def read_page_number(text: str) -> int:
    return int(text) if text.isdigit() and int(text) > 0 else 1


# Returns an id -> name lookup for the given user ids (empty ids are ignored).
def read_names(db: Session, user_ids: set) -> dict[str, str]:
    user_ids = {user_id for user_id in user_ids if user_id}
    return {u.id: u.name for u in db.scalars(select(User).where(User.id.in_(user_ids)))}


# Returns an office id -> office name lookup.
def read_office_names(db: Session) -> dict[int, str]:
    return {office.id: office.name for office in db.scalars(select(Office))}


# Returns one page of visible accounts plus the total match count and page numbers.
def list_accounts(db: Session, user: User, q: str, status: str, page_text: str, view: str = "") -> dict:
    mark_broken_ptps(db)
    query = accounts_visible_to(user)
    queue = view == "queue"
    if queue:
        query = query.where(Account.status.not_in(FINAL_STATUSES))
    q = q.strip()
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(
            Account.customer_name.ilike(pattern),
            Account.mobile.ilike(pattern),
            Account.loan_no.ilike(pattern),
        ))
    if status in STATUSES:
        query = query.where(Account.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    last_page = max(1, -(-total // PAGE_SIZE))  # divide and round up
    page = min(read_page_number(page_text), last_page)
    if queue:  # due follow-ups first (empty dates last), then biggest outstanding
        query = query.order_by(Account.next_followup.asc().nulls_last(), Account.outstanding.desc(), Account.id)
    else:
        query = query.order_by(Account.outstanding.desc(), Account.id)
    accounts = db.scalars(query.limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)).all()
    return {
        "accounts": accounts, "total": total, "view": view if queue else "", "page": page, "last_page": last_page,
        "names": read_names(db, {a.owner_id for a in accounts}),
        "offices": read_office_names(db),
    }


# Returns one account with its histories, or None when the user is not allowed to see it.
def get_account_page(db: Session, user: User, account_id: int) -> dict | None:
    mark_broken_ptps(db)
    account = db.scalars(accounts_visible_to(user).where(Account.id == account_id)).first()
    if account is None:
        return None
    calls = db.scalars(select(CallLog).where(CallLog.account_id == account_id).order_by(CallLog.id.desc())).all()
    promises = db.scalars(select(Ptp).where(Ptp.account_id == account_id).order_by(Ptp.id.desc())).all()
    payments = db.scalars(select(Payment).where(Payment.account_id == account_id).order_by(Payment.id.desc())).all()
    history = db.scalars(
        select(AllocationHistory).where(AllocationHistory.account_id == account_id).order_by(AllocationHistory.id.desc())
    ).all()
    ids = {account.owner_id, account.manager_id}
    ids |= {row.user_id for row in calls + promises + payments}
    for row in history:
        ids |= {row.from_user_id, row.to_user_id, row.by_user_id}
    return {
        "account": account, "calls": calls, "promises": promises, "payments": payments,
        "history": history, "names": read_names(db, ids), "dispositions": DISPOSITIONS,
        "can_log_call": user.role == "caller" and account.status not in FINAL_STATUSES,
        "can_record_payment": user.role == "caller" and account.status not in FINAL_STATUSES,
        "office_name": read_office_names(db).get(account.office_id, ""),
    }
