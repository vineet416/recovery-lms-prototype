import csv
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Account, Office, User

CHUNK_SIZE = 1000  # 1,000 rows x 20 columns = 20,000 values, under Postgres limit of 65,535
REQUIRED_COLUMNS = [
    "loan_no", "portfolio", "seller_bank", "customer_name", "mobile", "email", "city",
    "state", "office", "language", "product", "original_amount", "outstanding",
    "npa_date", "last_payment_date", "status",
]


# Turns a CSV money text like "125200" into a Decimal; raises ValueError if it is not a valid amount.
def read_money(text: str) -> Decimal:
    try:
        amount = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError("bad number")
    if not amount.is_finite() or amount < 0:
        raise ValueError("bad number")
    return amount


# Turns "2020-12-19" into a date, or None when blank; raises ValueError if the date is wrong.
def read_date(text: str) -> date | None:
    text = text.strip()
    return date.fromisoformat(text) if text else None


# Returns a name -> id lookup for offices and an office id -> manager ids lookup.
def read_lookups(db: Session) -> tuple[dict[str, int], dict[int, list[str]]]:
    office_ids = {office.name: office.id for office in db.scalars(select(Office))}
    managers_by_office: dict[int, list[str]] = {}
    for manager in db.scalars(select(User).where(User.role == "manager").order_by(User.id)):
        managers_by_office.setdefault(manager.office_id, []).append(manager.id)
    return office_ids, managers_by_office


# Turns one CSV row into a table row, or returns None when the row is bad and must be skipped.
def clean_row(row: dict, office_ids: dict, managers_by_office: dict, deal_count: dict):
    loan_no = (row["loan_no"] or "").strip()
    name = (row["customer_name"] or "").strip()
    mobile = (row["mobile"] or "").strip()
    office_id = office_ids.get((row["office"] or "").strip())
    managers = managers_by_office.get(office_id)
    if not (loan_no and name and mobile and managers):
        return None
    try:
        original = read_money(row["original_amount"])
        outstanding = read_money(row["outstanding"])
        npa_date = read_date(row["npa_date"])
        last_payment_date = read_date(row["last_payment_date"])
    except ValueError:
        return None
    turn = deal_count.get(office_id, 0)  # round-robin: next manager of this office
    deal_count[office_id] = turn + 1
    optional = {key: (row[key] or "").strip() or None for key in
                ["portfolio", "seller_bank", "email", "city", "state", "language", "product"]}
    return {
        **optional, "loan_no": loan_no, "customer_name": name, "mobile": mobile,
        "office_id": office_id, "original_amount": original, "outstanding": outstanding,
        "npa_date": npa_date, "last_payment_date": last_payment_date, "status": "New",
        "manager_id": managers[turn % len(managers)], "owner_id": None,
        "total_paid": 0, "next_followup": None,
    }


# Inserts one chunk of rows in a single statement and skips loan numbers that already exist.
def insert_chunk(db: Session, rows: list[dict]) -> None:
    statement = insert(Account.__table__).values(rows).on_conflict_do_nothing(index_elements=["loan_no"])
    db.execute(statement)


# Counts all accounts in the database.
def count_accounts(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Account))


# Loads an accounts CSV (already opened as text) and returns inserted, duplicates and skipped counts.
def load_accounts_csv(db: Session, text_file) -> dict:
    reader = csv.DictReader(text_file)
    missing = [name for name in REQUIRED_COLUMNS if name not in (reader.fieldnames or [])]
    if missing:
        raise ValueError("The file is missing these columns: " + ", ".join(missing))
    office_ids, managers_by_office = read_lookups(db)
    count_before, deal_count = count_accounts(db), {}
    valid_rows, skipped, chunk = 0, 0, []
    for row in reader:
        clean = clean_row(row, office_ids, managers_by_office, deal_count)
        if clean is None:
            skipped += 1
            continue
        chunk.append(clean)
        valid_rows += 1
        if len(chunk) == CHUNK_SIZE:
            insert_chunk(db, chunk)
            chunk = []
    if chunk:
        insert_chunk(db, chunk)
    db.commit()
    inserted = count_accounts(db) - count_before
    return {"inserted": inserted, "duplicates": valid_rows - inserted, "skipped": skipped}
