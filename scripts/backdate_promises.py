from datetime import date, timedelta

from sqlalchemy import select, update

from app.core.database import SessionLocal
from app.models import Account, Ptp


# Demo helper: moves every Pending promise date and its account follow-up to yesterday so the Broken rule can be shown.
def main() -> None:
    yesterday = date.today() - timedelta(days=1)
    with SessionLocal() as db:
        pending_accounts = select(Ptp.account_id).where(Ptp.state == "Pending")
        db.execute(update(Account).where(Account.id.in_(pending_accounts)).values(next_followup=yesterday))
        result = db.execute(update(Ptp).where(Ptp.state == "Pending").values(promise_date=yesterday))
        db.commit()
        print(f"Backdated {result.rowcount} pending promise(s) to yesterday.")


if __name__ == "__main__":
    main()
