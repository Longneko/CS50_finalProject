class Ingredient(object):
    """An ingredient that is a part of a dish.

    :param name: A string, name of the ingredient.
    :params amt_units: A number, number of measurement units comprising amount of ingredient.
    :params amt_unit_type: A string, measurement unit used to denote amount of ingredient.
    :param allergies: A set, contains widespread allergies where the ingredient is known
        to be the allergen.
    :param tags: A set, contains arbitrary tags e.g. 'spicy'.
    """
    def __init__(self, name, amt_units=0, amt_unit_type="kg", allergies=set(), tags=set()):
        self.name = name
        self.amt_units = amt_units
        self.amt_unit_type = amt_unit_type
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

    @property
    def amt_units(self):
        """Get amount as number of measurement units"""
        return self._amt_units

    @amt_units.setter
    def amt_units(self, value):
        try:
            if value and value >= 0:
                self._amt_units = value
        except ValueError:
            raise RuntimeError("amt_units must be a positive number")
