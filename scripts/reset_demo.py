import argparse

import app.models  # noqa: F401  (importing registers all tables on Base)
from app.core.database import Base, engine
from scripts.seed import seed_everything


# Drops every table, creates them again and seeds offices and users.
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-accounts", action="store_true", help="skip loading accounts")
    args = parser.parse_args()
    Base.metadata.drop_all(engine)
    print("Dropped all tables.")
    seed_everything(load_accounts=not args.no_accounts)
    print("Demo reset done.")


if __name__ == "__main__":
    main()
