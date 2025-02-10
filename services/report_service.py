import csv
from config import DB_PATH

EXPENSE_FILE = DB_PATH

def get_expense_report():
    with open(EXPENSE_FILE, mode='r') as file:
        reader = csv.reader(file)
        expenses = list(reader)
    return expenses