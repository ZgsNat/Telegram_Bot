import os

def initialize_db():
    if not os.path.exists("database"):
        os.makedirs("database")
    db_file = "database/expenses.db"
    if not os.path.exists(db_file):
        open(db_file, 'w').close()