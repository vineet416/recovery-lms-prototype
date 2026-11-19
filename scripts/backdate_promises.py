from datetime import date, timedelta

from sqlalchemy import update

from app.core.database import SessionLocal
from app.models import Ptp


# Demo helper: moves every Pending promise date to yesterday so the Broken rule can be shown.
def main() -> None:
    with SessionLocal() as db:
        result = db.execute(
            update(Ptp).where(Ptp.state == "Pending").values(promise_date=date.today() - timedelta(days=1))
        )
        db.commit()
        print(f"Backdated {result.rowcount} pending promise(s) to yesterday.")


if __name__ == "__main__":
    main()
