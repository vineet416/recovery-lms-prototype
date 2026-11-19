from sqlalchemy import bindparam, func, insert, select, update
from sqlalchemy.orm import Session

from app.features.accounts.service import PAGE_SIZE, read_names, read_page_number
from app.features.accounts.visibility import accounts_visible_to
from app.models import Account, AllocationHistory, User


# Returns the callers this user may allocate to: a manager's own team, or every caller for the head.
def list_callers_for(db: Session, user: User) -> list[User]:
    query = select(User).where(User.role == "caller").order_by(User.name)
    if user.role == "manager":
        query = query.where(User.manager_id == user.id)
    return list(db.scalars(query))


# Returns one page of accounts to allocate, filtered to unallocated or allocated ones.
def list_allocation_accounts(db: Session, user: User, which: str, page_text: str) -> dict:
    which = which if which in ("unallocated", "allocated") else "unallocated"
    query = accounts_visible_to(user)
    query = query.where(Account.owner_id.is_(None) if which == "unallocated" else Account.owner_id.is_not(None))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    last_page = max(1, -(-total // PAGE_SIZE))  # divide and round up
    page = min(read_page_number(page_text), last_page)
    query = query.order_by(Account.outstanding.desc(), Account.id)
    accounts = db.scalars(query.limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)).all()
    return {
        "accounts": accounts, "total": total, "page": page, "last_page": last_page, "which": which,
        "names": read_names(db, {a.owner_id for a in accounts}),
        "callers": list_callers_for(db, user),
    }


# Gives the ticked accounts to one caller and writes a history row for each. Returns how many moved.
def assign_accounts(db: Session, user: User, account_ids: list[int], caller_id: str) -> int:
    if not account_ids:
        raise ValueError("Please tick at least one account.")
    caller = next((c for c in list_callers_for(db, user) if c.id == caller_id), None)
    if caller is None:
        raise ValueError("Please choose a caller from the list.")
    accounts = db.scalars(accounts_visible_to(user).where(Account.id.in_(account_ids))).all()
    if not accounts:
        raise ValueError("None of the ticked accounts can be allocated by you.")
    for account in accounts:
        db.add(AllocationHistory(
            account_id=account.id, from_user_id=account.owner_id, to_user_id=caller.id, by_user_id=user.id,
        ))
        account.owner_id = caller.id
        account.manager_id = caller.manager_id
    db.commit()
    return len(accounts)


# Deals the manager's unallocated accounts round-robin to the team callers. Returns how many were given out.
def auto_allocate(db: Session, user: User) -> int:
    callers = list_callers_for(db, user)
    if not callers:
        raise ValueError("You have no callers in your team.")
    account_ids = db.scalars(
        accounts_visible_to(user).where(Account.owner_id.is_(None)).order_by(Account.id).with_only_columns(Account.id)
    ).all()
    if not account_ids:
        raise ValueError("You have no unallocated accounts.")
    updates, history = [], []
    for position, account_id in enumerate(account_ids):
        caller = callers[position % len(callers)]
        updates.append({"b_id": account_id, "b_owner": caller.id})
        history.append({
            "account_id": account_id, "from_user_id": None, "to_user_id": caller.id, "by_user_id": user.id,
        })
    # Callers of a manager already have that manager as manager_id, so only owner_id changes here.
    owner_update = update(Account.__table__).where(Account.__table__.c.id == bindparam("b_id")).values(
        owner_id=bindparam("b_owner"),
    )
    for start in range(0, len(updates), 1000):
        db.execute(owner_update, updates[start:start + 1000])
        db.execute(insert(AllocationHistory.__table__), history[start:start + 1000])
    db.commit()
    return len(account_ids)
