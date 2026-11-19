import csv
import random

OUTPUT_FILE = "data/big_accounts.csv"
ROW_COUNT = 100_000
OFFICES = ["Jogeshwari", "Dadar", "Bangalore"]
OFFICE_WEIGHTS = [4485, 2988, 2527]  # same mix as accounts_10000.csv
HEADER = [
    "loan_no", "portfolio", "seller_bank", "customer_name", "mobile", "email", "city",
    "state", "office", "language", "product", "original_amount", "outstanding",
    "npa_date", "last_payment_date", "status",
]
FIRST_NAMES = ["Rahul", "Mahesh", "Priya", "Anita", "Suresh", "Kavita", "Imran", "Sneha"]
LAST_NAMES = ["More", "Naik", "Shah", "Patil", "Khan", "Iyer", "Reddy", "Joshi"]
PRODUCTS = ["Personal Loan", "Credit Card", "Auto Loan", "Home Loan"]


# Builds one fake account row; the number makes the loan number and mobile unique.
def make_row(number: int) -> list:
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    original = random.randint(20, 500) * 1000
    outstanding = original + random.randint(-20, 100) * 100
    office = random.choices(OFFICES, OFFICE_WEIGHTS)[0]
    portfolio = random.choice(["PF-A", "PF-B"])
    return [
        f"LNX{number:06d}", portfolio, "Bank Alpha" if portfolio == "PF-A" else "Bank Beta",
        name, str(6000000000 + number), f"{name.lower().replace(' ', '.')}{number}@example.com",
        "Mumbai", "Maharashtra", office, random.choice(["Hindi", "Marathi", "English"]),
        random.choice(PRODUCTS), original, outstanding,
        f"20{random.randint(19, 22)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        f"20{random.randint(18, 21)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        "New",
    ]


# Writes the big test file used for the 1,00,000 row upload demo.
def main() -> None:
    random.seed(42)
    with open(OUTPUT_FILE, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(HEADER)
        for number in range(100_001, 100_001 + ROW_COUNT):
            writer.writerow(make_row(number))
    print(f"Wrote {ROW_COUNT} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
