from collections import namedtuple

from backend.DBEntry import DBEntry, to_db_obj_name
from backend.Allergy import Allergy
from backend.Recipe import Recipe

class User(DBEntry):
    """An end-user representation that contains individual settings.

    :param name: Inherits from DBEntry.
    :param password_hash: A string. Password hash provided by an external function.
    :param is_admin: A boolean. Whether user has access to admin functional.
    :param allergies: A set of Allergy objects. Recipes containing ingredients causing these will
        not appear in user's meal plans.
    :param allergies: A set of Recipe objects. Recipess that are currently in the meal plan
        of the user.
    :param db: Inherits from DBEntry.
    :param id: Inherits from DBEntry.
    """
    table_main = "users"

    # meals are not called recipes because it is planned for meals to eventually have extended
    # functional like multiple helpings per recipe, etc.
    def __init__(self, name, password_hash, is_admin=False, allergies=set(), meals=set(), db=None,
                 id=None):
        super().__init__(name=name, db=db, id=id)
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.meals = meals
        self.allergies = allergies

    @classmethod
    def from_db(cls, db, id=None, name=None):
        """Search db for user entry by id or name (in that priorty) and return constructed object.
        Returns None if id is not found.
        """
        user = super().from_db(db=db, id=id, name=name)

        if not user:
            return None
        id = user.id

        # Constructing allergies set
        needle = (id,)
        db.c.execute('SELECT allergy_id as id FROM user_allergies WHERE user_id = ?', needle)
        rows = db.c.fetchall()
        allergies = {Allergy.from_db(db, row["id"]) for row in rows}

        # Constructing meals set
        needle = (id,)
        db.c.execute('SELECT recipe_id as id FROM user_meals WHERE user_id = ?', needle)
        rows = db.c.fetchall()
        meals = {Recipe.from_db(db, row["id"]) for row in rows}

        user.allergies = allergies
        user.meals = meals

        return user

    def new_to_db(self):
        """Write a new user to the DB. Return id assigned by the DB."""
        table_main = to_db_obj_name(self.table_main)

        # Inserting values to the main table
        user = (self.name, self.password_hash, self.is_admin)
        self.db.c.execute(f'INSERT INTO "{table_main}" (name, password_hash, is_admin) '
                           'VALUES (?, ?, ?)', user)

        # Remembering id assigned by the DB
        new_row_id = (self.db.c.lastrowid,)
        self.db.c.execute(f'SELECT id FROM {table_main} WHERE rowid = ?', new_row_id)
        row = self.db.c.fetchone()
        id = row["id"]

        # inserting allergies to the associative table
        allergies = {(id, a.id) for a in self.allergies}
        self.db.c.executemany('INSERT INTO user_allergies (user_id, allergy_id) VALUES (?, ?)',
                              allergies)

        # inserting meals to the associative table
        meals = {(id, m.id) for m in self.meals}
        self.db.c.executemany('INSERT INTO user_meals (user_id, recipe_id) VALUES (?, ?)', meals)

        return id

    def edit_in_db(self):
        """Edit existing DB user to match current object state. Return number of affected rows."""
        table_main = to_db_obj_name(self.table_main)
        rows_affected = 0

        # Updating values to the main table
        user = (self.name, self.password_hash, self.is_admin, self.id)
        self.db.c.execute(f'UPDATE "{table_main}" SET name = ?, password_hash = ?, is_admin = ? '
                           'WHERE id = ?', user)
        rows_affected += self.db.c.rowcount

        # Allergies block
        # Constructing sets of the users's old and new allergies' ids
        new_allergy_ids = {a.id for a in self.allergies}
        needle = (self.id,)
        old_allergies = self.db.c.execute('SELECT allergy_id as id FROM user_allergies WHERE '
                                          'user_id = ?', needle).fetchall()
        old_allergy_ids = {a["id"] for a in old_allergies}

        # Removing allergies missing in the new set
        to_remove = {(self.id, a_id) for a_id in old_allergy_ids - new_allergy_ids}
        self.db.c.executemany(
            'DELETE FROM user_allergies WHERE user_id = ? AND allergy_id = ?', to_remove)
        rows_affected += self.db.c.rowcount

        # Adding allergies missing in the old set
        to_add = {(self.id, a_id) for a_id in new_allergy_ids - old_allergy_ids}
        self.db.c.executemany(
            'INSERT INTO user_allergies (user_id, allergy_id) VALUES (?, ?)',
            to_add
        )
        rows_affected += self.db.c.rowcount

        # Meals block
        # Constructing sets of the users's old and new recipes' ids
        new_recipe_ids = {r.id for r in self.meals}
        needle = (self.id,)
        old_recipes = self.db.c.execute('SELECT recipe_id as id FROM user_meals WHERE '
                                          'user_id = ?', needle).fetchall()
        old_recipe_ids = {r["id"] for r in old_recipes}

        # Removing recipes missing in the new set
        to_remove = {(self.id, r_id) for r_id in old_recipe_ids - new_recipe_ids}
        self.db.c.executemany(
            'DELETE FROM user_meals WHERE user_id = ? AND recipe_id = ?', to_remove)
        rows_affected += self.db.c.rowcount

        # Adding recipes missing in the old set
        to_add = {(self.id, r_id) for r_id in new_recipe_ids - old_recipe_ids}
        self.db.c.executemany(
            'INSERT INTO user_meals (user_id, recipe_id) VALUES (?, ?)',
            to_add
        )
        rows_affected += self.db.c.rowcount

        return rows_affected

    @classmethod
    def get_summary(cls, db, name_sort=False):
        """"Return summary table for all user objects in DB as dictionary list.
        id: user id.
        name: user name.
        allergies: list of allergies.
        meals: list of meals.
        dependents: number of other class entries referencing this id as a foreign key.
            Currently none but might change in the future.

        param name_sort: A boolean. If True, summary will be recursively sorted by
            object name ascending.
        """
        summary = []

        # Get main table data omitting the password_hash
        db.c.execute('SELECT id, name, is_admin '
                     'FROM users '
                     'ORDER BY id ASC'
        )
        for db_row in db.c.fetchall():
            row = {x: y for x, y in zip(db_row.keys(), db_row)}
            row["is_admin"] = bool(row["is_admin"])
            summary.append(row)


        # Allergies block
        # Get allergy lists
        db.c.execute(
            'SELECT user_allergies.user_id, allergies.name as allergy_name '
            'FROM user_allergies '
            'LEFT JOIN allergies ON user_allergies.allergy_id = allergies.id '
            'ORDER BY user_allergies.user_id ASC'
        )
        db_rows = db.c.fetchall()
        if db_rows:
            it_summary = iter(summary)
            s_row = next(it_summary)
            for db_row in db_rows:
                while not db_row["user_id"] == s_row["id"]:
                    # Ensure at least an empty 'cell' exists for this ingredient before moving to next
                    try:
                        s_row["allergies"]
                    except KeyError:
                        s_row["allergies"] = []
                    s_row = next(it_summary)

                try:
                    s_row["allergies"].append(db_row["allergy_name"])
                except KeyError:
                    s_row["allergies"] = [db_row["allergy_name"]]

            # Fill remaining rows with empty allergy lists
            finished = False
            while not finished:
                try:
                    s_row = next(it_summary)
                    s_row["allergies"] = []
                except StopIteration:
                    finished = True

        # Meals block
        # Get allergy lists
        db.c.execute(
            'SELECT user_meals.user_id, recipes.name as meal_name '
            'FROM user_meals '
            'LEFT JOIN recipes ON user_meals.recipe_id = recipes.id '
            'ORDER BY user_meals.user_id ASC'
        )
        db_rows = db.c.fetchall()
        if db_rows:
            it_summary = iter(summary)
            s_row = next(it_summary)
            for db_row in db_rows:
                while not db_row["user_id"] == s_row["id"]:
                    # Ensure at least an empty 'cell' exists for this ingredient before moving to next
                    try:
                        s_row["meals"]
                    except KeyError:
                        s_row["meals"] = []
                    s_row = next(it_summary)

                try:
                    s_row["meals"].append(db_row["meal_name"])
                except KeyError:
                    s_row["meals"] = [db_row["meal_name"]]

            # Fill remaining rows with empty allergy lists
            finished = False
            while not finished:
                try:
                    s_row = next(it_summary)
                    s_row["meals"] = []
                except StopIteration:
                    finished = True


        # Set dependents currently non-existent
        for row in summary:
            row["dependents"] = 0


        if name_sort:
            summary.sort(key=lambda x: x["name"].lower())
            for row in summary:
                row["allergies"].sort(key=str.lower)
                row["meals"].sort(key=str.lower)


        return summary

    # password_hash made name mangled for JSON encoder to omit it
    @property
    def password_hash(self):
        """Get user's password_hash"""
        return self.__password_hash

    @password_hash.setter
    def password_hash(self, value):
        self.__password_hash = value

    @property
    def is_admin(self):
        """Get entry's password_hash"""
        return self._is_admin

    # sqlite stores bools as 0 or 1
    @is_admin.setter
    def is_admin(self, value):
        self._is_admin = bool(value)
