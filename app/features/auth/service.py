from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import check_password
from app.models import User


# Returns the user if the username exists and the password matches, otherwise None.
def check_login(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username.strip()))
    if user is None or not check_password(password, user.password_hash):
        return None
    return user
