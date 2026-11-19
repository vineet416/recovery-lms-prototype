from sqlalchemy import func, select

from app.models import Account, AllocationHistory, CallLog


# Counts the history rows of one account.
def count_history(db, account_id: int) -> int:
    return db.scalar(select(func.count()).where(AllocationHistory.account_id == account_id))


# Finds a New unallocated account of a manager (not given to anyone yet).
def free_account_of(db, manager_id: str) -> int:
    query = select(Account.id).where(Account.manager_id == manager_id, Account.owner_id.is_(None))
    return db.scalars(query.order_by(Account.id.desc())).first()


# A manager gives an account to a team caller; owner, manager and history are saved.
def test_manager_assigns_to_team_caller(client_for, db, fresh_account):
    account_id = free_account_of(db, "M01")
    client_for("manager1").post("/allocation/assign", data={"account_ids": [account_id], "caller_id": "C001"})
    account = fresh_account(account_id)
    assert (account.owner_id, account.manager_id) == ("C001", "M01")
    assert count_history(db, account_id) == 1


# Reassigning keeps the old history row and the call log.
def test_reassign_keeps_history_and_calls(client_for, db, open_account_for, fresh_account):
    account_id = open_account_for("C001")
    client_for("caller1").post(f"/accounts/{account_id}/call", data={"disposition": "Busy"})
    client_for("manager1").post("/allocation/assign", data={"account_ids": [account_id], "caller_id": "C002"})
    assert fresh_account(account_id).owner_id == "C002"
    assert count_history(db, account_id) == 2
    assert db.scalar(select(func.count()).where(CallLog.account_id == account_id)) == 1


# A manager cannot give accounts to a caller of another team.
def test_manager_cannot_use_other_teams_caller(client_for, db, team_callers, fresh_account):
    account_id = free_account_of(db, "M01")
    other_caller = team_callers("M04")[0]
    client_for("manager1").post("/allocation/assign", data={"account_ids": [account_id], "caller_id": other_caller})
    assert fresh_account(account_id).owner_id is None
    assert count_history(db, account_id) == 0


# The head can give an account to any caller.
def test_head_assigns_to_any_caller(client_for, db, team_callers, fresh_account):
    account_id = free_account_of(db, "M01")
    caller_id = team_callers("M04")[0]
    client_for("head").post("/allocation/assign", data={"account_ids": [account_id], "caller_id": caller_id})
    account = fresh_account(account_id)
    assert (account.owner_id, account.manager_id) == (caller_id, "M04")


# Auto-allocate splits the unallocated accounts evenly and leaves owned accounts alone.
def test_auto_allocate_is_even_and_skips_owned(client_for, db, team_callers, open_account_for, fresh_account):
    callers = team_callers("M06")
    owned_id = open_account_for(callers[-1])
    client_for("manager6").post("/allocation/auto")
    db.expire_all()
    per_caller = db.execute(
        select(Account.owner_id, func.count()).where(Account.manager_id == "M06").group_by(Account.owner_id)
    ).all()
    counts = [count for owner, count in per_caller if owner in callers and owner != callers[-1]]
    assert max(counts) - min(counts) <= 1
    assert fresh_account(owned_id).owner_id == callers[-1]
    assert db.scalar(select(func.count()).where(Account.manager_id == "M06", Account.owner_id.is_(None))) == 0


# The coo and callers cannot allocate.
def test_coo_and_caller_cannot_allocate(client_for):
    for username in ["coo", "caller1"]:
        assert client_for(username).post("/allocation/assign", data={}).status_code == 403
        assert client_for(username).post("/allocation/auto").status_code == 403
