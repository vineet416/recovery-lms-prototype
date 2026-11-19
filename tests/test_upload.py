import os
import time

import pytest
from sqlalchemy import func, select

from app.models import Account, User
from scripts import make_big_csv

HEADER = ("loan_no,portfolio,seller_bank,customer_name,mobile,email,city,state,office,language,"
          "product,original_amount,outstanding,npa_date,last_payment_date,status\n")


# Builds one CSV line for a test account.
def make_line(loan_no: str, name: str = "Test Person", office: str = "Dadar", outstanding: str = "5000") -> str:
    return f"{loan_no},PF-A,Bank Alpha,{name},9000000001,t@example.com,Pune,MH,{office},Hindi,Loan,9000,{outstanding},2021-01-01,2020-06-01,New\n"


# Uploads CSV text as the given user and returns the response.
def upload(client, text: str):
    return client.post("/upload", files={"file": ("accounts.csv", text, "text/csv")})


# Good rows are inserted, a repeated loan number is a duplicate, bad rows are skipped.
def test_upload_counts(client_for, db):
    lines = [make_line("TST001"), make_line("TST002"), make_line("TST001"), make_line("TST003", name=""),
             make_line("TST004", office="Nowhere"), make_line("TST005", outstanding="abc")]
    page = upload(client_for("head"), HEADER + "".join(lines)).text
    assert "Inserted: <strong>2</strong>" in page
    assert "Duplicates (already in the system): <strong>1</strong>" in page
    assert "Skipped bad rows: <strong>3</strong>" in page
    account = db.scalars(select(Account).where(Account.loan_no == "TST001")).one()
    assert (account.status, account.owner_id, account.total_paid) == ("New", None, 0)
    assert db.get(User, account.manager_id).office_id == account.office_id


# Uploading the same file again gives only duplicates.
def test_reupload_is_all_duplicates(client_for):
    text = HEADER + make_line("TST010") + make_line("TST011")
    upload(client_for("head"), text)
    page = upload(client_for("head"), text).text
    assert "Inserted: <strong>0</strong>" in page and "<strong>2</strong>" in page


# Only the head can upload.
def test_only_head_can_upload(client_for):
    for username in ["manager1", "caller1", "coo", "cs1"]:
        assert upload(client_for(username), HEADER + make_line("TST020")).status_code == 403


# A file with missing columns shows a friendly message, not a crash.
def test_wrong_columns_show_message(client_for):
    response = upload(client_for("head"), "loan_no,name\nX1,Someone\n")
    assert response.status_code == 400 and "missing these columns" in response.text


# Loads the 1,00,000 row file and checks all rows go in within about a minute.
@pytest.mark.slow
def test_upload_one_lakh_rows(client_for, db):
    if not os.path.exists(make_big_csv.OUTPUT_FILE):
        make_big_csv.main()
    before = db.scalar(select(func.count()).select_from(Account))
    started = time.time()
    with open(make_big_csv.OUTPUT_FILE, "rb") as big_file:
        response = client_for("head").post("/upload", files={"file": ("big.csv", big_file, "text/csv")})
    seconds = time.time() - started
    assert "Inserted: <strong>100000</strong>" in response.text
    assert db.scalar(select(func.count()).select_from(Account)) == before + 100_000
    print(f"1,00,000 rows loaded in {seconds:.1f} seconds")
    assert seconds < 60
