from collections import namedtuple

from backend.DBEntry import DBEntry

class Recipe(DBEntry):
    """A recipe of a dish.

    :param contents: A list of Content namedtuples, ingredients and their amounts
        that comprise the dish.
    :param instructions: A string, instructios on how to cook the dish.
    """
    def __init__(self, name, db_id=None, contents=[], instructions=""):
        super().__init__(name, db_id)
        self.contents = contents
        self.instructions = instructions

    # <TODO> Contents representation to be reworked? Add allergies repr
    def __repr__(self):
        contents = ''
        for content in self.contents:
            contents += '\n  {} - {}'.format(content.ingredient.name, content.units,)
            if content.unit_type:
                contents += ' ' + content.unit_type

        return ('<Recipe {}\n'
                ' db_id: {}\n'
                ' Contents:'
                ' {}\n'
                '>'
                ).format(self.name, self.db_id, contents, end='')

# constructor validation from kindall's answer at
# https://stackoverflow.com/questions/42146268/create-custom-namedtuple-type-with-extra-features
ContentTuple = namedtuple('Content', 'ingredient units unit_type')

class Content(ContentTuple):
    """Represents quantity or amount of a specific ingredient in a dish"""
    __slots__ = ()
    def __new__(cls, ingredient, units, unit_type=None):
        try:
            if not units or units < 0:
                raise ValueError("units must be a positive number")
        except:
            raise RuntimeError("units must be a positive number")

        return ContentTuple.__new__(cls, ingredient, units, unit_type)

    def _replace(self, **kwargs):
        try:
            if not kwargs['units'] or kwargs['units'] < 0:
                raise ValueError("units must be a positive number")
        except ValueError:
            raise RuntimeError("units must be a positive number")
        except KeyError:
            pass

        return super()._replace(**kwargs)
