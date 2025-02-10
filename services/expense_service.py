import csv
from config import DB_PATH

EXPENSE_FILE = DB_PATH

def add_expense_entry(amount: str, description: str):
    with open(EXPENSE_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([amount, description])