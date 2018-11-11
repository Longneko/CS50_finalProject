# allergens to be renamed to ingredient_allergies
from collections import namedtuple

from backend.DBEntry import DBEntry, to_db_obj_name
from backend.Allergy import Allergy
from backend.IngredientCategory import IngredientCategory

class Ingredient(DBEntry):
    """An ingredient that can be used a recipe"""
    table_main = "ingredients"

    def __init__(self, name, category, allergies=set(), db=None, id=None):
        """Constructor. Returns functional object.

        :param name: Inherits from DBEntry.
        :param category: An IngredientCategory, category of the ingredient.
        :param allergies: A set of Allergies. Contains allergies where
            the ingredient is known to be the allergen.
        :param db: Inherits from DBEntry.
        :param id: Inherits from DBEntry.
        """
        super().__init__(name, db, id)
        self.category = category
        self.allergies = allergies

    @classmethod
    def from_db(cls, db, id=None, name=None):
        """Search db for ingredient entry by id and return constructed object.
        Returns None if id is not found.
        """
        db_attrs = cls.get_db_attrs(db, id, name)

        if not db_attrs:
            return None
        id = db_attrs["id"]

        # Constructing category
        category_id = db_attrs["category_id"]
        del db_attrs["category_id"]
        category = IngredientCategory.from_db(db, category_id)

        # Constructing allergies set
        needle = (id,)
        db.c.execute('SELECT allergy_id as id FROM allergens WHERE ingredient_id = ?', needle)
        rows = db.c.fetchall()
        allergies = set()
        for row in rows:
            allergies.add(Allergy.from_db(db, row["id"]))

        return cls(db=db, category=category, allergies=allergies, **db_attrs)

    def new_to_db(self):
        """Write a new ingredient to the DB. Return id assigned by the DB."""
        table_main = to_db_obj_name(self.table_main)

        # Inserting values to the main table
        ingredient = (self.name, self.category.id )
        self.db.c.execute(f'INSERT INTO "{table_main}" (name, category_id) VALUES (?, ?)',
                          ingredient)

        # Remembering id assigned by the DB
        new_row_id = (self.db.c.lastrowid,)
        self.db.c.execute(f'SELECT id FROM {table_main} WHERE rowid = ?', new_row_id)
        row = self.db.c.fetchone()
        id = row["id"]

        # inserting allergies to the associative table
        allergies = {(id, a.id) for a in self.allergies}
        self.db.c.executemany("INSERT INTO allergens (ingredient_id, allergy_id) VALUES (?, ?)",
                          allergies)

        return id

    def edit_in_db(self):
        """Edit existing DB ingredient to match current object state. Return number of
        affected rows.
        """
        table_main = to_db_obj_name(self.table_main)
        rows_affected = 0

        # Updating values to the main table
        ingredient = (self.name, self.category.id, self.id)
        self.db.c.execute(f'UPDATE "{table_main}" SET name = ?, category_id = ? WHERE id = ?',
                          ingredient)
        rows_affected += self.db.c.rowcount


        # Constructing sets of the ingredient's old and new allergies' ids
        new_allergy_ids = {a.id for a in self.allergies}
        needle = (self.id,)
        old_allergies = self.db.c.execute('SELECT allergy_id as id FROM allergens WHERE '
                                       'ingredient_id = ?', needle).fetchall()
        old_allergy_ids = {a["id"] for a in old_allergies}

        # Removing allergies missing in the new set
        to_remove = {(self.id, a_id) for a_id in old_allergy_ids - new_allergy_ids}
        self.db.c.executemany('DELETE FROM allergens WHERE ingredient_id = ? AND allergy_id = ?',
                              to_remove)
        rows_affected += self.db.c.rowcount

        # Adding allergies missing in the old set
        to_add = {(self.id, a_id) for a_id in new_allergy_ids - old_allergy_ids}
        self.db.c.executemany('INSERT INTO allergens (ingredient_id, allergy_id) VALUES (?, ?)',
                              to_add)
        rows_affected += self.db.c.rowcount

        return rows_affected

    @classmethod
    def get_summary(cls, db, name_sort=False):
        """"Return summary table for all Ingredient objects in DB as dictionary list.
        id: ingredient id.
        name: ingredient name.
        category: ingredient category name.
        allergies: list of allergies.
        dependents: number of other class entries referencing this id as a foreign key.

        param name_sort: A boolean. If True, summary will be recursively sorted by
            object name ascending.
        """
        summary = []

        # Get main table data and category names
        db.c.execute(
            'SELECT ingredients.id, ingredients.name, ingredient_categories.name as category '
            'FROM ingredients '
            'LEFT JOIN ingredient_categories '
            '  ON ingredients.category_id = ingredient_categories.id '
            'ORDER BY ingredients.id ASC'
        )
        for db_row in db.c.fetchall():
            row = {x: y for x, y in zip(db_row.keys(), db_row)}
            summary.append(row)


        # Get allergy lists
        db.c.execute(
            'SELECT allergens.ingredient_id, allergies.name as allergy_name '
            'FROM allergens '
            'LEFT JOIN allergies ON allergens.allergy_id = allergies.id '
            'ORDER BY allergens.ingredient_id ASC'
        )
        it_summary = iter(summary)
        row = next(it_summary)
        for db_row in db.c.fetchall():
            while not db_row["ingredient_id"] == row["id"]:
                # Ensure at least an empty 'cell' exists for this ingredient before moving to next
                try:
                    row["allergies"]
                except KeyError:
                    row["allergies"] = []
                row = next(it_summary)

            try:
                row["allergies"].append(db_row["allergy_name"])
            except KeyError:
                row["allergies"] = [db_row["allergy_name"]]

        # Fill remaining rows with empty allergy lists
        finished = False
        while not finished:
            try:
                row = next(it_summary)
                row["allergies"] = []
            except StopIteration:
                finished = True


        # Get dependents
        db.c.execute(
            'SELECT ingredient_id, COUNT(recipe_id) as dependents FROM recipe_contents '
            'GROUP BY ingredient_id '
            'ORDER BY ingredient_id ASC'
        )
        it_summary = iter(summary)
        row = next(it_summary)
        for db_row in db.c.fetchall():
            while not db_row["ingredient_id"] == row["id"]:
                # Set dependents = 0 for ingredients that don't exist in recipe_contents table
                try:
                    row["dependents"]
                except KeyError:
                    row["dependents"] = 0

                row = next(it_summary)

            row["dependents"] = db_row["dependents"]

        # Fill remaining rows with dependents = 0
        finished = False
        while not finished:
            try:
                row = next(it_summary)
                row["dependents"] = 0
            except StopIteration:
                finished = True


        if name_sort:
            summary.sort(key=lambda x: x["name"].lower())
            for row in summary:
                row["allergies"].sort(key=str.lower)


        return summary
