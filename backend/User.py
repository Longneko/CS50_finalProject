from collections import namedtuple

from backend.DBEntry import DBEntry, validate_db_id


class IdSet(set):
    """A set that accepts only valid db_id as its items"""
    def __init__(self, iterable=()):
        for db_id in iterable:
            if not validate_db_id(db_id):
                raise ValueError("db_id must be a positive integer")
        super().__init__(iterable)

    def add(self, db_id):
        if not validate_db_id(db_id):
            raise ValueError("db_id must be a positive integer")
        super().add(db_id)


class User(DBEntry):
    """An end-user representation that contains individual settings.

    :param allergies: A set of Allergy objects. Recipes containing ingredients causing these will
        not appear in user's meal plans.
    :param meals: A set of integers - db_id of recipes currently in the user's meal plan.
    :param is_admin: A boolean. Whether user has access to admin functional.
    """
    # meals is later to be expanded to contains number of helpings per each meal
    def __init__(self, name, password_hash, db_id=None, allergies=set(), meals=IdSet(), is_admin=False):
        super().__init__(name, db_id)
        self.password_hash = password_hash
        self.allergies = allergies
        self.meals = meals
        self.is_admin = is_admin

    def __str__(self):
        return ("<User {}\n"
                " db_id: {}\n"
                " allergies: {}\n"
                ">"
                ).format(self.name, self.db_id, self.allergies)
