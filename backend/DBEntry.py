import json
from collections import namedtuple


class DBEntry(object):
    """A basic object entry in a DB with mandatory id and a name fields

    :param name: A string, name of the entry.
    :param db_id: An integer, id of the entry in the SQLite DB.
        Objects not yet stored in the DB must have None as their db_id.
    """
    def __init__(self, name, db_id=None):
        self.name = name
        self.db_id = db_id

    @property
    def name(self):
        """Get entry's name"""
        return self._name

    @name.setter
    def name(self, value):
        if not validate_name(value):
            raise RuntimeError("name must be a non-empty string")
        self._name = value

    @property
    def db_id(self):
        """Get entry's id"""
        return self._db_id

    @db_id.setter
    def db_id(self, value):
        if not validate_db_id(value):
            raise RuntimeError("db_id must be a positive integer or None")
        self._db_id = value

    def __str__(self):
        return ("{} ({})").format(self.name, self.db_id)

    def toJSONifiable(self):
        return {key.lstrip("_"): val for key, val in vars(self).items()}


class IngredientCategory(DBEntry):
    def __str__(self):
        return ("{} ({})").format(self.name, self.db_id)


class Allergy(DBEntry):
    def __str__(self):
        return ("{} ({})").format(self.name, self.db_id)


class FoodEncoder(json.JSONEncoder):
    def default(self, obj): # pylint: disable=E0202
        if isinstance(obj, (set)):
            return list(obj)
        try:
            return obj.toJSONifiable()
        except:
            pass
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def validate_db_id(db_id):
    try:
        if not db_id is None and db_id < 1:
            return False
    except:
        return False
    return True

def validate_name(name):
    if not (name and isinstance(name, str)):
        return False
    return True
