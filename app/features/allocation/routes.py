from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.flash import set_flash
from app.core.templates import templates
from app.features.allocation.service import assign_accounts, auto_allocate, list_allocation_accounts
from app.models import User

router = APIRouter()


# Shows the allocation screen: filter, tick boxes and the caller drop-down.
@router.get("/allocation")
def allocation_page(
    request: Request,
    which: str = "unallocated",
    page: str = "1",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_role(user, ["manager", "head"])
    context = {"user": user, **list_allocation_accounts(db, user, which, page)}
    return templates.TemplateResponse(request, "allocation.html", context)


# Gives the ticked accounts to the chosen caller, then goes back to the same filter.
@router.post("/allocation/assign")
def allocation_assign(
    request: Request,
    account_ids: list[int] = Form([]),
    caller_id: str = Form(""),
    which: str = Form("unallocated"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_role(user, ["manager", "head"])
    try:
        count = assign_accounts(db, user, account_ids, caller_id)
        set_flash(request, f"{count} account(s) allocated.", "success")
    except ValueError as error:
        db.rollback()
        set_flash(request, str(error), "error")
    return RedirectResponse(f"/allocation?which={quote(which)}", status_code=303)


# Splits all of the manager's unallocated accounts evenly between the team callers.
@router.post("/allocation/auto")
def allocation_auto(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_role(user, ["manager"])
    try:
        count = auto_allocate(db, user)
        set_flash(request, f"{count} account(s) shared equally between your callers.", "success")
    except ValueError as error:
        db.rollback()
        set_flash(request, str(error), "error")
    return RedirectResponse("/allocation", status_code=303)
