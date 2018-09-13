from collections import namedtuple

class Recipe(object):
    """A recipe of a dish.

    :param name: A string, name of the recipe.
    :param contents: A list of Content namedtuples, ingredients and their amounts
        that comprise the dish.
    :param instructions: A string, instructios on how to cook the dish.
    """
    def __init__(self, name, id=None, contents=[], instructions=""):
        self.name = name
        self.id = id
        self.contents = contents
        self.instructions = instructions

    @property
    def name(self):
        """Get current name"""
        return self._name

    @name.setter
    def name(self, value):
        if not value:
            raise RuntimeError("name must be a non-empty string")
        self._name = value


# constructor validation from kindall's answer at
# https://stackoverflow.com/questions/42146268/create-custom-namedtuple-type-with-extra-features
ContentTuple = namedtuple('Content', 'ingredient units unit_type')

class Content(ContentTuple):
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
            if kwargs['units'] < 0:
                raise ValueError("units must be a positive number")
        except ValueError:
            raise ValueError("units must be a positive number")
        except KeyError:
            pass

        return super()._replace(**kwargs)
