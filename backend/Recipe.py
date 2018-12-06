from collections import namedtuple

from backend.DBEntry import DBEntry, to_db_obj_name
from backend.Ingredient import Ingredient


class Recipe(DBEntry):
    """A recipe of a dish. Consists of ingredients with optional amount (in optional units)."""
    table_main = "recipes"
    associations = [
        ("user_meals","recipe_id", False),
        ("recipe_contents","recipe_id", True)
    ]

    def __init__(self, name, instructions="", contents=set(), db=None, id=None):
        """Constructor. Returns functional object.

        :param name: Inherits from DBEntry.
        :param instructions: A string, instructios on how to cook the dish.
        :param contents: A set of Content namedtuples - ingredients and their amounts
            that comprise the dish.
        :param db: Inherits from DBEntry.
        :param id: Inherits from DBEntry.
        """
        super().__init__(name=name, db=db, id=id)
        self.instructions = instructions
        self.contents = contents

    @classmethod
    def from_db(cls, db, id=None, name=None):
        """Search db for recipe entry by id or name (in that priority) and return constructed
        object. Returns None if id is not found.
        """
        recipe = super().from_db(db=db, id=id, name=name)

        if not recipe:
            return None
        id = recipe.id

        # Constructing contents set
        needle = (id,)
        db.c.execute(
            'SELECT ingredient_id, amount, units FROM recipe_contents '
            'WHERE recipe_id = ?',
            needle
        )
        rows = db.c.fetchall()
        contents = set()
        for row in rows:
            ingredient = Ingredient.from_db(db, row["ingredient_id"])
            content = Content(ingredient, row["amount"], row["units"])
            contents.add(content)

        recipe.contents = contents
        return recipe

    def new_to_db(self):
        """Write a new recipe entry to the DB. Return id assigned by the DB."""
        table_main = to_db_obj_name(self.table_main)

        # Inserting values to the main table
        recipe = (self.name, self.instructions)
        self.db.c.execute(f'INSERT INTO "{table_main}" (name, instructions) VALUES (?, ?)',
                          recipe)

        # Remembering id assigned by the DB
        new_row_id = (self.db.c.lastrowid,)
        self.db.c.execute(f'SELECT id FROM "{table_main}" WHERE rowid = ?', new_row_id)
        row = self.db.c.fetchone()
        id = row["id"]

        # inserting contents to the associative table
        contents = {(id, c.ingredient.id, c.amount, c.units) for c in self.contents}
        self.db.c.executemany(
            'INSERT INTO recipe_contents (recipe_id, ingredient_id, amount, units) '
            '  VALUES (?, ?, ?, ?)',
            contents
        )

        return id

    def edit_in_db(self):
        """Edit existing DB recipe to match current object state. Return number of
        affected rows.
        """
        table_main = to_db_obj_name(self.table_main)
        rows_affected = 0

        # Updating values to the main table
        recipe = (self.name, self.instructions, self.id)
        self.db.c.execute(f'UPDATE "{table_main}" SET name = ?, instructions = ? WHERE id = ?',
                          recipe)
        rows_affected += self.db.c.rowcount


        # Constructing sets of the recipe's old and new contents' ingredient ids
        new_ingredient_ids = {c.ingredient.id for c in self.contents}
        needle = (self.id,)
        old_contents = self.db.c.execute('SELECT ingredient_id as id FROM recipe_contents WHERE '
                                         'recipe_id = ?', needle).fetchall()
        old_ingredient_ids = {c["id"] for c in old_contents}

        # Removing contents missing in the new set
        to_remove = {(self.id, i_id) for i_id in old_ingredient_ids - new_ingredient_ids}
        self.db.c.executemany('DELETE FROM recipe_contents WHERE recipe_id = ? AND ingredient_id = ?',
                              to_remove)
        rows_affected += self.db.c.rowcount

        # Adding contents missing in the old set
        new_contents = {c for c in self.contents
                        if c.ingredient.id in new_ingredient_ids - old_ingredient_ids}
        to_add = {(self.id, c.ingredient.id, c.amount, c.units) for c in new_contents}
        self.db.c.executemany(
            'INSERT INTO recipe_contents (recipe_id, ingredient_id, amount, units) '
            '  VALUES (?, ?, ?, ?)',
            to_add
        )
        rows_affected += self.db.c.rowcount

        # Updating contents present in both the old and the new sets
        updated_contents = self.contents - new_contents
        to_update = {(c.amount, c.units, self.id, c.ingredient.id) for c in updated_contents}
        self.db.c.executemany(
            'UPDATE recipe_contents SET amount = ?, units = ? '
            '  WHERE recipe_id = ? AND ingredient_id = ?',
            to_update
        )

        return rows_affected

    @classmethod
    def get_summary(cls, db, name_sort=False):
        """"Return summary table for Recipe objects in DB as dictionary list.
        id: recipe db_id.
        name: recipe name.
        instructions: instructions on how to prepare the dish.
        contents: list of contents (ingredient name, amount, units).
        dependents: number of other class entries referencing this id as a foreign key.

        param name_sort: A boolean. If True, summary will be recursively sorted by
            object name ascending.
        """
        summary = []

        # Get main table data
        db.c.execute('SELECT id, name, instructions '
                     'FROM recipes '
                     'ORDER BY id ASC'
        )
        for db_row in db.c.fetchall():
            row = {x: y for x, y in zip(db_row.keys(), db_row)}
            summary.append(row)


        # Get content lists
        db.c.execute(
            'SELECT recipe_contents.recipe_id, ingredients.name as ingredient, '
            '  recipe_contents.amount, recipe_contents.units '
            'FROM recipe_contents '
            'LEFT JOIN ingredients ON recipe_contents.ingredient_id = ingredients.id '
            'ORDER BY recipe_id ASC'
        )
        db_rows = db.c.fetchall()
        if db_rows:
            it_summary = iter(summary)
            s_row = next(it_summary)
            for db_row in db_rows:
                while not db_row["recipe_id"] == s_row["id"]:
                    # Ensure at least an empty 'cell' exists for this recipe before moving to next
                    try:
                        s_row["contents"]
                    except KeyError:
                        s_row["contents"] = []
                    s_row = next(it_summary)

                content = {
                    "ingredient": db_row["ingredient"],
                    "amount"    : db_row["amount"],
                    "units"     : db_row["units"],
                }
                try:
                    s_row["contents"].append(content)
                except KeyError:
                    s_row["contents"] = [content]

            # Fill remaining rows with empty content lists
            finished = False
            while not finished:
                try:
                    s_row = next(it_summary)
                    s_row["contents"] = []
                except StopIteration:
                    finished = True


        # Get dependents
        db.c.execute(
            'SELECT recipe_id, COUNT(user_id) as dependents FROM user_meals '
            'GROUP BY recipe_id '
            'ORDER BY recipe_id ASC'
        )
        db_rows = db.c.fetchall()
        if db_rows:
            it_summary = iter(summary)
            s_row = next(it_summary)
            for db_row in db_rows:
                while not db_row["recipe_id"] == s_row["id"]:
                    # Set dependents = 0 for ingredients that don't exist in recipe_contents table
                    try:
                        s_row["dependents"]
                    except KeyError:
                        s_row["dependents"] = 0

                    s_row = next(it_summary)

                s_row["dependents"] = db_row["dependents"]

            # Fill remaining rows with dependents = 0
            finished = False
            while not finished:
                try:
                    s_row = next(it_summary)
                    s_row["dependents"] = 0
                except StopIteration:
                    finished = True

        if name_sort:
            summary.sort(key=lambda x: x["name"].lower())
            for row in summary:
                try:
                    row["contents"].sort(key=lambda x: x["ingredient"].lower())
                except KeyError:
                    pass


        return summary

    def toJSONifiable(self):
        dct = super().toJSONifiable()
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
        except TypeError:
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
