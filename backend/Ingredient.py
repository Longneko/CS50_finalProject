class Ingredient(object):
    """An ingredient that is a part of a dish.

    :param name: A string, name of the ingredient.
    :param category: A string, category of the ingredient.
    :param id: An integer, id of the ingredient in the SQLite DB.
    :param allergies: A set, contains widespread allergies where the ingredient is known
        to be the allergen.
    :param tags: A set, contains arbitrary tags e.g. 'spicy'.
    """
    def __init__(self, name, category, id=None, allergies=set(), tags=set()):
        self.name = name
        self.category = category
        self.id = id
        self.allergies = allergies
        self.tags = tags

    @property
    def name(self):
        """Get current name"""
        return self._name

    @name.setter
    def name(self, value):
        if not value:
            raise RuntimeError("name must be a non-empty string")
        self._name = value
