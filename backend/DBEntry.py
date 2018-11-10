import json
import inspect

from backend.DBHandler import DBHandler, to_db_obj_name


class DBEntry(object):
    """An abstract object entry in a DB with mandatory id and a name fields.
    Should only be used as a base class and on its own.

    :attr table_main: A string. Name of the table where class object entries are stored in DB.
        Is set to None for DBEntry since this is an abstract and is not stored in DB.
    """
    table_main = None

    def __init__(self, name, db=None, id=None):
        """Constructor. Returns functional object.

        :param name: A string, name of the entry.
        :param db: A DBHandler. Object that manages conenction to the DB.
            Defaults to None but must be assigned before saving object to DB.
        :param id: An integer, id of the entry in the SQLite3 DB.
            Defaults to None which means the object is not yet stored in the DB.
        """
        self.name = name
        self.db = db
        self.id = id

    @classmethod
    def get_db_attrs(cls, db, id):
        """Search for entry by id. Return dictionary of values necesary for constructor.
        Returns None if id is not found.

        Entry is searched in the table with name defined by the 'table_main' class attribue.
        DBEntry
        """
        if not cls.exists_in_db(db, id):
            return None

        table_main = to_db_obj_name(cls.table_main)

        query = f'SELECT * FROM "{table_main}" WHERE id = ?'
        needle = (id,)
        row = db.c.execute(query, needle).fetchone()

        db_data = {x: y for x, y in zip(row.keys(), row)}

        return db_data

    @classmethod
    def from_db(cls, db, id):
        """Search db for class object entry by id and return constructed object.
        Returns None if id is not found.
        """
        db_attrs = cls.get_db_attrs(db, id)

        if not db_attrs:
            return None
        return cls(db=db, **db_attrs)

    @classmethod
    def exists_in_db(cls, db, id):
        """Check if and entry of this object type with provided id exists in the specified db"""
        if db.exists(cls.table_main, id=id):
            return True
        return False

    @property
    def name(self):
        """Get entry's name"""
        return self._name

    @name.setter
    def name(self, value):
        if not validate_name(value):
            raise ValueError("name must be a non-empty string")
        self._name = value

    @property
    def db(self):
        """Get entry's DBHandler"""
        return self.__db

    @db.setter
    def db(self, value):
        if value and not isinstance(value, DBHandler):
            raise ValueError("db must be a DBHandler object")
        self.__db = value

    @property
    def id(self):
        """Get entry's id"""
        return self._id

    @id.setter
    def id(self, value):
        if not validate_id(value):
            raise ValueError("id must be a positive integer or None")
        self._id = value

    def write_to_db(self):
        if not self.id:
            self.id = self.new_to_db()
        else:
            self.edit_in_db()

        self.db.conn.commit()

    def new_to_db(self):
        """Write a new entry to the DB. Return id assigned by the DB"""
        table_main = to_db_obj_name(self.table_main)
        allergy = (self.name,)

        self.db.c.execute(f'INSERT INTO "{table_main}" (name) VALUES (?)', allergy)
        new_row_id = (self.db.c.lastrowid,)

        row = self.db.c.execute(f"SELECT id FROM {table_main} WHERE rowid = ?", new_row_id).fetchone()

        return row["id"]

    def edit_in_db(self):
        """Edit existing DB entry to match current object state. Return number of affected rows"""
        table_main = to_db_obj_name(self.table_main)
        allergy = (self.name, self.id)
        self.db.c.execute(f'UPDATE "{table_main}" SET name = ? WHERE id = ?', allergy)
        return self.db.c.rowcount

    def toJSONifiable(self):
        """Return a JSONifiable dictionary of the object's attributes. Omits name mangled (__attr) attributes
        and trims underscore from private (_attr) attribute names.
        """
        return {x.lstrip("_"): y
                for x, y in vars(self).items()
                if not is_mangled(x, self.__class__)
        }


class Allergy(DBEntry):
    """An allergy that an ingredient may cause and users may list to avoid meals with
    such ingredients.

    All methods and instance attributes are inherited from DBEntry.
    """
    table_main = "allergies"


class IngredientCategory(DBEntry):
    """Categorizes ingredients.

    All methods and instance attributes are inherited from DBEntry.
    """
    table_main = "ingredient_categories"


class FoodEncoder(json.JSONEncoder):
    """JSON encoder that encodes sets as list and tries to call toJSONifiable() method for other
    classes.
    """
    def default(self, obj): # pylint: disable=E0202
        if isinstance(obj, (set)):
            return list(obj)
        try:
            return obj.toJSONifiable()
        except:
            pass
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def validate_id(id):
    try:
        if not id is None and id < 1:
            return False
    except:
        return False
    return True

def validate_name(name):
    if not (name and isinstance(name, str)):
        return False
    return True

def is_mangled(attr_name, classinfo):
    classes = inspect.getmro(classinfo)
    for c in classes:
        if attr_name.startswith("_" + c.__name__ + "__"):
            return True
    return False
