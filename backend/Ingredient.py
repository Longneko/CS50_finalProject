from collections import namedtuple

class Ingredient(object):
    """An ingredient that is a part of a dish.

    :param name: A string, name of the ingredient.
    :param category: A string, category of the ingredient.
    :param db_id: An integer, db_id of the ingredient in the SQLite DB.
    :param allergies: A set, contains widespread allergies where
        the ingredient is known to be the allergen.
    """
    def __init__(self, name, category, db_id=None, allergies=set()):
        self.name = name
        self.category = category
        self.db_id = db_id
        self.allergies = allergies

    @property
    def name(self):
        """Get ingredient name"""
        return self._name

    @name.setter
    def name(self, value):
        if not value:
            raise RuntimeError("name must be a non-empty string")
        self._name = value

    @property
    def db_id(self):
        """Get ingredient db_id"""
        return self._db_id

    @db_id.setter
    def db_id(self, value):
        try:
            if not value or value < 1:
                raise ValueError("db_id must be a positive integer")
        except:
            raise RuntimeError("db_id must be a positive integer")
        self._db_id = value

    def __repr__(self):
        return ('<Ingredient {!r}\n'
                'category: {!r}\n'
                'db_id: {!r}\n'
                'allergies: {!r}>'
                ).format(self.name, self.category, self.db_id, self.allergies)

# constructor validation from kindall's answer at
# https://stackoverflow.com/questions/42146268/create-custom-namedtuple-type-with-extra-features
IdAndNameTuple = namedtuple('Dual', 'db_id name')

class Dual(IdAndNameTuple):
    """Simple objects stored in DB as id and name only.
    E.g. ingredient category or allergy."""
    __slots__ = ()
    def __new__(cls, db_id, name):
        if not validate_id(db_id):
            raise RuntimeError("db_id must be a positive integer")
        if not validate_name(name):
            raise RuntimeError("name must be a non-empty string")

        return IdAndNameTuple.__new__(cls, db_id, name)

    def _replace(self, **kwargs):
        try:
            if not validate_id(kwargs['db_id']):
                raise RuntimeError("db_id must be a positive integer")
        except KeyError:
            pass

        try:
            if not validate_id(kwargs['name']):
                raise RuntimeError("name must be a non-empty string")
        except KeyError:
            pass

        return super()._replace(**kwargs)

    def validate_id(value):
        try:
            if not value or value < 1:
                return False
        except:
            return False
        return True

    def validate_name(value):
        try:
            if not (value and isinstance(value, str)):
                return False
        except:
            return False
        return True
