from collections import namedtuple

from backend.DBEntry import DBEntry

class Ingredient(DBEntry):
    """An ingredient that is a part of a dish.

    :param category: A DBEntry, category of the ingredient.
    :param allergies: A set, contains widespread allergies (as DBEntry) where
        the ingredient is known to be the allergen.
    """
    def __init__(self, name, category, db_id=None, allergies=set()):
        super().__init__(name, db_id)
        self.category = category
        self.allergies = allergies

    def __str__(self):
        return ('<Ingredient {}\n'
                ' category: {}\n'
                ' db_id: {}\n'
                ' allergies: {}\n'
                '>'
                ).format(self.name, self.category, self.db_id, self.allergies)
