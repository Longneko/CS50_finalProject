from backend.Ingredient import Ingredient

class Dish(object):
    """An ingredient that is a part of a dish.

    :param name: A string, name of the dish.
    :param ingredients: A list, Ingredients that comprise the dish.
    :param instructions: A string, instructios on how to cook the dish.
    """
    def __init__(self, name, ingredients=[], instructions=""):
        self.name = name
        self.ingredients = ingredients
        self.instructions = instructions
        self.helpings = 1

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
    def helpings(self):
        return self._helpings

    @helpings.setter
    def helpings(self, value):
        """Set a positive integer number of helpings changing ingredients' amounts accordingly"""
        try:
            value = int(value)
            if not value > 0:
                raise RuntimeError("helpings must be a positive integer")
        except ValueError:
            raise RuntimeError("helpings must be a positive integer")

        if not hasattr(self, "helpings"):
            self._helpings = value
        else:
            factor = value / self._helpings
            for ingredient in self.ingredients:
                print(ingredient.__dict__)
                ingredient.amt_units *= factor
            self._helpings = value
