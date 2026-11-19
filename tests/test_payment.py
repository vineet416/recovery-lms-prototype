from datetime import date

from sqlalchemy import func, select

from app.models import CallLog, Payment, Ptp


# Counts payments on one account.
def count_payments(db, account_id: int) -> int:
    return db.scalar(select(func.count()).where(Payment.account_id == account_id))


# A part payment raises total_paid and sets Part-paid, but outstanding never changes.
def test_part_payment(client_for, open_account_for, fresh_account):
    account_id = open_account_for("C001")
    outstanding = fresh_account(account_id).outstanding
    client_for("caller1").post(f"/accounts/{account_id}/payment", data={"amount": "1"})
    account = fresh_account(account_id)
    assert (account.status, account.total_paid, account.outstanding) == ("Part-paid", 1, outstanding)


# Paying the full outstanding closes the account.
def test_full_payment_closes(client_for, open_account_for, fresh_account):
    account_id = open_account_for("C001")
    full = str(fresh_account(account_id).outstanding)
    client_for("caller1").post(f"/accounts/{account_id}/payment", data={"amount": full})
    assert fresh_account(account_id).status == "Closed"


# Ticking settlement settles the account.
def test_settlement(client_for, open_account_for, fresh_account):
    account_id = open_account_for("C001")
    client_for("caller1").post(f"/accounts/{account_id}/payment", data={"amount": "1", "is_settlement": "on"})
    assert fresh_account(account_id).status == "Settled"


# A payment turns the Pending promise into Kept.
def test_payment_keeps_pending_promise(client_for, db, open_account_for):
    account_id = open_account_for("C001")
    caller = client_for("caller1")
    caller.post(f"/accounts/{account_id}/call", data={
        "disposition": "Promise to pay", "promise_amount": "100", "promise_date": date.today().isoformat()})
    caller.post(f"/accounts/{account_id}/payment", data={"amount": "100"})
    assert db.scalars(select(Ptp.state).where(Ptp.account_id == account_id)).all() == ["Kept"]


# A Closed account refuses new payments and new calls.
def test_closed_account_is_read_only(client_for, db, open_account_for, fresh_account):
    account_id = open_account_for("C001")
    caller = client_for("caller1")
    caller.post(f"/accounts/{account_id}/payment", data={"amount": str(fresh_account(account_id).outstanding)})
    caller.post(f"/accounts/{account_id}/payment", data={"amount": "1"})
    caller.post(f"/accounts/{account_id}/call", data={"disposition": "Busy"})
    assert count_payments(db, account_id) == 1
    assert db.scalar(select(func.count()).where(CallLog.account_id == account_id)) == 0


# A zero or empty amount is rejected.
def test_bad_amount_is_rejected(client_for, db, open_account_for):
    account_id = open_account_for("C001")
    for amount in ["0", "", "abc"]:
        client_for("caller1").post(f"/accounts/{account_id}/payment", data={"amount": amount})
    assert count_payments(db, account_id) == 0


# Only the owning caller can record a payment.
def test_only_owner_caller_can_pay(client_for, db, open_account_for):
    account_id = open_account_for("C001")
    for username in ["manager1", "head", "coo", "cs1"]:
        assert client_for(username).post(f"/accounts/{account_id}/payment", data={"amount": "1"}).status_code == 403
    client_for("caller2").post(f"/accounts/{account_id}/payment", data={"amount": "1"})
    assert count_payments(db, account_id) == 0
