import argparse
import csv

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import DEMO_PASSWORD
from app.core.database import SessionLocal, create_tables
from app.core.security import hash_password
from app.features.upload.service import load_accounts_csv
from app.models import Office, User

USERS_CSV = "data/users_seed.csv"
ACCOUNTS_CSV = "data/accounts_10000.csv"


# Reads every row of the users CSV into a list of dictionaries.
def read_users_csv() -> list[dict]:
    with open(USERS_CSV, newline="") as csv_file:
        return list(csv.DictReader(csv_file))


# Adds one office per unique office name and returns a name -> id lookup.
def seed_offices(db: Session, rows: list[dict]) -> dict[str, int]:
    for name in sorted({row["office"] for row in rows}):
        db.add(Office(name=name))
    db.flush()
    return {office.name: office.id for office in db.scalars(select(Office))}


# Adds all users with the same demo password; managers go first so callers can point to them.
def seed_users(db: Session, rows: list[dict], office_ids: dict[str, int]) -> None:
    password_hash = hash_password(DEMO_PASSWORD)
    managers_first = sorted(rows, key=lambda row: row["role"] != "manager")
    for row in managers_first:
        db.add(User(
            id=row["user_id"],
            name=row["name"],
            role=row["role"],
            office_id=office_ids[row["office"]],
            manager_id=row["manager_id"] or None,
            username=row["username"] or row["role"],  # head and coo have no username in the CSV
            password_hash=password_hash,
        ))
        db.flush()


# Prints how many offices and users of each role are in the database.
def print_counts(db: Session) -> None:
    print("offices:", db.scalar(select(func.count()).select_from(Office)))
    for role in ["manager", "caller", "head", "coo", "customer_service"]:
        count = db.scalar(select(func.count()).select_from(User).where(User.role == role))
        print(f"{role}s:" if role in ("manager", "caller") else f"{role}:", count)


# Creates tables, then loads offices, users and (unless skipped) the accounts CSV.
def seed_everything(load_accounts: bool = True) -> None:
    create_tables()
    rows = read_users_csv()
    with SessionLocal() as db:
        office_ids = seed_offices(db, rows)
        seed_users(db, rows, office_ids)
        db.commit()
        print_counts(db)
        if load_accounts:
            with open(ACCOUNTS_CSV, newline="", encoding="utf-8-sig") as csv_file:
                print("accounts:", load_accounts_csv(db, csv_file))


# Reads the command line options and runs the seed.
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--if-empty", action="store_true", help="do nothing if users exist")
    parser.add_argument("--no-accounts", action="store_true", help="skip loading accounts")
    args = parser.parse_args()
    create_tables()
    with SessionLocal() as db:
        has_users = db.scalar(select(func.count()).select_from(User)) > 0
    if args.if_empty and has_users:
        print("Users already exist, nothing to seed.")
        return
    seed_everything(load_accounts=not args.no_accounts)


if __name__ == "__main__":
    main()
