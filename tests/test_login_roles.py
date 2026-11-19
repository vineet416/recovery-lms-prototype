from sqlalchemy import func, select

from app.features.accounts.visibility import accounts_visible_to
from app.models import Account, User


# Counts the accounts a user is allowed to see.
def count_visible(db, user_id: str) -> int:
    query = accounts_visible_to(db.get(User, user_id))
    return db.scalar(select(func.count()).select_from(query.subquery()))


# Every seeded role can log in and is sent to the home page.
def test_each_role_can_log_in(client_for):
    for username in ["head", "coo", "manager1", "caller1", "cs1"]:
        response = client_for(username).get("/")
        assert response.status_code == 303 and response.headers["location"].startswith("/accounts")


# A wrong password shows a friendly message and a 401.
def test_wrong_password_shows_message(client_for):
    client = client_for("caller1")
    response = client.post("/login", data={"username": "caller1", "password": "nope"})
    assert response.status_code == 401 and "Wrong username or password." in response.text


# Someone who is not logged in is sent to the login page.
def test_logged_out_user_goes_to_login(client_for):
    response = client_for("nobody").get("/accounts")
    assert response.status_code == 303 and response.headers["location"] == "/login"


# A caller cannot open another caller's account by URL, but can open their own.
def test_caller_cannot_open_other_callers_account(client_for, open_account_for):
    account_id = open_account_for("C001")
    assert client_for("caller1").get(f"/accounts/{account_id}").status_code == 200
    assert client_for("caller2").get(f"/accounts/{account_id}").status_code == 404


# A manager sees only own team accounts; a manager of another office gets 404.
def test_manager_cannot_open_other_teams_account(client_for, open_account_for):
    account_id = open_account_for("C001")
    assert client_for("manager1").get(f"/accounts/{account_id}").status_code == 200
    assert client_for("manager4").get(f"/accounts/{account_id}").status_code == 404


# Customer service sees only accounts of its own office.
def test_customer_service_sees_only_own_office(client_for, db, open_account_for):
    account_id = open_account_for("C001")  # C001 works in Jogeshwari
    assert client_for("cs1").get(f"/accounts/{account_id}").status_code == 200
    assert client_for("cs2").get(f"/accounts/{account_id}").status_code == 404
    cs_user = db.get(User, "S02")
    other_office = accounts_visible_to(cs_user).where(Account.office_id != cs_user.office_id)
    assert db.scalar(select(func.count()).select_from(other_office.subquery())) == 0
    assert count_visible(db, "S02") > 0


# Callers see only their own accounts; head and coo see every account.
def test_visible_counts_by_role(db, open_account_for):
    open_account_for("C001")
    total = db.scalar(select(func.count()).select_from(Account))
    assert count_visible(db, "C001") == db.scalar(select(func.count()).where(Account.owner_id == "C001"))
    assert count_visible(db, "C002") == db.scalar(select(func.count()).where(Account.owner_id == "C002"))
    assert count_visible(db, "U001") == total and count_visible(db, "U002") == total


# Pages a role may not open answer 403.
def test_blocked_pages_return_403(client_for):
    for username, path in [("caller1", "/upload"), ("caller1", "/allocation"), ("coo", "/upload"),
                           ("coo", "/allocation"), ("manager1", "/upload"), ("cs1", "/allocation")]:
        assert client_for(username).get(path).status_code == 403
    assert client_for("coo").post("/allocation/assign", data={}).status_code == 403
