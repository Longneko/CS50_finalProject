class Ingredient(object):
    """An ingredient that is a part of a dish.

    :param name: A string, name of the ingredient.
    :param category: A string, category of the ingredient.
    :param id: An integer, id of the ingredient in the SQLite DB.
    :param allergies: A set, contains widespread allergies where
        the ingredient is known to be the allergen.
    """
    def __init__(self, name, category, id=None, allergies=set()):
        self.name = name
        self.category = category
        self.id = id
        self.allergies = allergies

    @property
    def name(self):
        """Get current name"""
        return self._name

    @name.setter
    def name(self, value):
        if not value:
            raise RuntimeError("name must be a non-empty string")
        self._name = value

    def __repr__(self):
        return ('<Ingredient {!r}\n'
                'category: {!r}\n'
                'id: {!r}\n'
                'allergies: {!r}>'
                ).format(self.name, self.category, self.id, self.allergies)