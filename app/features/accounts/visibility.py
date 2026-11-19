from sqlalchemy import select
from sqlalchemy.sql import Select

from app.models import Account, User


# Returns the base query of accounts this user may see. Every account query starts from here.
def accounts_visible_to(user: User) -> Select:
    query = select(Account)
    if user.role == "caller":
        return query.where(Account.owner_id == user.id)
    if user.role == "manager":
        return query.where(Account.manager_id == user.id)
    if user.role in ("head", "coo"):
        return query
    if user.role == "customer_service":
        return query.where(Account.office_id == user.office_id)
    return query.where(Account.id == None)  # noqa: E711  (unknown role sees nothing)
