from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.constants import ROLES, STATUSES
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.templates import templates
from app.features.accounts.service import get_account_page, list_accounts
from app.models import User

router = APIRouter()


# Shows the searchable, paged list of accounts this user is allowed to see.
@router.get("/accounts")
def accounts_list(
    request: Request,
    q: str = "",
    status: str = "",
    page: str = "1",
    view: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_role(user, ["caller"] if view == "queue" else ROLES)
    context = {"user": user, "q": q, "status": status, "statuses": STATUSES}
    context.update(list_accounts(db, user, q, status, page, view))
    return templates.TemplateResponse(request, "accounts_list.html", context)


# Shows one account page, or a 404 page when the account is missing or not visible to this user.
@router.get("/accounts/{account_id}")
def account_detail(
    request: Request,
    account_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_role(user, ROLES)
    page_data = get_account_page(db, user, account_id)
    if page_data is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request, "account_detail.html", {"user": user, **page_data})
