import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.constants import DEMO_PASSWORD
from app.core.database import Base, SessionLocal, engine
from app.features.allocation.service import assign_accounts
from app.main import app
from app.models import Account, User
from scripts.seed import seed_everything


# Drops all tables and loads the demo data again (same as the reset_demo command).
def reset_database() -> None:
    Base.metadata.drop_all(engine)
    seed_everything()


# Resets the database before the first test and again after the last one, so demo data is restored.
@pytest.fixture(scope="session", autouse=True)
def fresh_database():
    reset_database()
    yield
    reset_database()


# Gives each test its own database session for checking results.
@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


# Gives a function: client_for("caller1") returns a test client that is already logged in.
@pytest.fixture
def client_for():
    def make_client(username: str) -> TestClient:
        client = TestClient(app, follow_redirects=False)
        client.post("/login", data={"username": username, "password": DEMO_PASSWORD})
        return client
    return make_client


# Gives a function: team_callers("M01") returns the ids of that manager's callers.
@pytest.fixture
def team_callers(db):
    def find_callers(manager_id: str) -> list[str]:
        return list(db.scalars(select(User.id).where(User.manager_id == manager_id).order_by(User.id)))
    return find_callers


# Gives a function: open_account_for("C001") hands a fresh New account to that caller and returns its id.
@pytest.fixture
def open_account_for(db):
    def give_account(caller_id: str) -> int:
        manager = db.get(User, db.get(User, caller_id).manager_id)
        query = select(Account.id).where(
            Account.manager_id == manager.id, Account.owner_id.is_(None), Account.status == "New",
        ).order_by(Account.id)
        account_id = db.scalars(query).first()
        assign_accounts(db, manager, [account_id], caller_id)
        return account_id
    return give_account


# Gives a function: fresh_account(id) reads the account again from the database.
@pytest.fixture
def fresh_account(db):
    def read_account(account_id: int) -> Account:
        db.expire_all()
        return db.get(Account, account_id)
    return read_account
