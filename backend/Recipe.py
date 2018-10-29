from collections import namedtuple

from backend.DBEntry import DBEntry

class Recipe(DBEntry):
    """A recipe of a dish.

    :param contents: A set of Content namedtuples - ingredients and their amounts
        that comprise the dish.
    :param instructions: A string, instructios on how to cook the dish.
    """
    def __init__(self, name, db_id=None, contents=set(), instructions=""):
        super().__init__(name, db_id)
        self.contents = contents
        self.instructions = instructions

    # <TODO> Contents representation to be reworked? Add allergies repr
    def __str__(self):
        contents = ""
        for content in self.contents:
            contents += "\n  {} - {}".format(content.ingredient.name, content.amount,)
            if content.units:
                contents += " " + content.units

        return ("<Recipe {}\n"
                " db_id: {}\n"
                " Contents:"
                " {}\n"
                " Instructions: {}>"
                ).format(self.name, self.db_id, contents, self.instructions, end="")

    def toJSONifiable(self):
        dct = dict(self.__dict__)
        contents_list = [item._asdict() for item in self.contents]
        dct["contents"] = contents_list
        return dct


# constructor validation from kindall"s answer at
# https://stackoverflow.com/a/42146452
ContentTuple = namedtuple("ContentTuple", "ingredient amount units")
class Content(ContentTuple):
    """Represents quantity or amount of a specific ingredient in a dish"""
    __slots__ = ()
    def __new__(cls, ingredient, amount, units=None):
        try:
            if not amount >= 0:
                raise ValueError("amount must be a positive number")
        except:
            raise RuntimeError("amount must be a positive number")

        return ContentTuple.__new__(cls, ingredient, amount, units)

    def _replace(self, **kwargs):
        try:
            if not kwargs["amount"] >= 0:
                raise ValueError("amount must be a positive number")
        except ValueError:
            raise RuntimeError("amount must be a positive number")
        except KeyError:
            pass

        return super()._replace(**kwargs)

    def toJSONifiable(self):
        return self._asdict()
