import io

from fastapi import APIRouter, Depends, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.templates import templates
from app.features.upload.service import load_accounts_csv
from app.models import User

router = APIRouter()


# Shows the upload form (head only).
@router.get("/upload")
def upload_form(request: Request, user: User = Depends(get_current_user)):
    require_role(user, ["head"])
    return templates.TemplateResponse(request, "upload.html", {"user": user})


# Loads the chosen CSV file and shows the summary, or a friendly message if the file is wrong.
@router.post("/upload")
def upload_submit(
    request: Request,
    file: UploadFile | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_role(user, ["head"])
    context = {"user": user}
    if file is None or not file.filename:
        context["message"] = "Please choose a CSV file first."
        return templates.TemplateResponse(request, "upload.html", context, status_code=400)
    try:
        text_file = io.TextIOWrapper(file.file, encoding="utf-8-sig", newline="")
        context["summary"] = load_accounts_csv(db, text_file)
    except (ValueError, UnicodeDecodeError) as error:
        db.rollback()
        context["message"] = str(error) if isinstance(error, ValueError) else "That file is not a readable CSV."
        return templates.TemplateResponse(request, "upload.html", context, status_code=400)
    return templates.TemplateResponse(request, "upload.html", context)
