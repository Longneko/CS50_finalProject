import sqlite3
from werkzeug.security import generate_password_hash

from backend.DBHandler import DBHandler
from backend.User import User

db = DBHandler()

USER = "admin"

try:
    db.create_schema()
    user = User(name=USER, password_hash=generate_password_hash(USER), is_admin=True, db=db)
    user.write_to_db()

    print("New DB initialized successfully, 'admin' user created.")
except sqlite3.OperationalError:
    print("The DB already exists and has a schema. Operation aborted.")
