from collections import namedtuple

from backend.DBEntry import DBEntry

class User(DBEntry):
    """AN end-user representation that contains individual settings"""
    def __init__(self, name, password_hash, db_id=None, allergies=set()):
        super().__init__(name, db_id)
        self.password_hash = password_hash
        self.allergies = allergies

    def __str__(self):
        return ("<User {}\n"
                " db_id: {}\n"
                " allergies: {}\n"
                ">"
                ).format(self.name, self.db_id, self.allergies)
