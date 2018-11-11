import sqlite3

# from backend.DBEntry import IngredientCategory, Allergy
# from backend.Ingredient import Ingredient
# from backend.Recipe import Recipe, Content
# from backend.User import User, IdSet

DEFAULT_DB_PATH = "backend/food.db"

class DBHandler(object):
    """Handles storage and retrieval of within a DB.

    :param db_path: A string, path to the target DB.
    """
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON;")
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def create_schema(self):
        """Create the required schema in an empty DB"""
        self.c.executescript("""
                CREATE TABLE ingredient_categories(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE ingredients(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE,
                  category_id INTEGER NOT NULL,
                  FOREIGN KEY (category_id) REFERENCES ingredient_categories(id)
                );

                CREATE TABLE allergies(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE ingredient_allergies(
                  ingredient_id INTEGER NOT NULL,
                  allergy_id INTEGER NOT NULL,
                  PRIMARY KEY (allergy_id, ingredient_id),
                  FOREIGN KEY (allergy_id) REFERENCES allergies(id),
                  FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
                );

                CREATE TABLE recipes(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE,
                  instructions TEXT
                );

                CREATE TABLE recipe_contents(
                  recipe_id INTEGER NOT NULL,
                  ingredient_id INTEGER NOT NULL,
                  amount INTEGER NOT NULL,
                  units TEXT DEFAULT NULL,
                  PRIMARY KEY (recipe_id, ingredient_id),
                  FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                  FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
                );

                CREATE TABLE users(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE,
                  password_hash TEXT NOT NULL,
                  is_admin INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE user_allergies(
                  user_id INTEGER NOT NULL,
                  allergy_id INTEGER NOT NULL,
                  PRIMARY KEY (allergy_id, user_id),
                  FOREIGN KEY (allergy_id) REFERENCES allergies(id),
                  FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE user_meals(
                  user_id INTEGER,
                  recipe_id INTEGER,
                  PRIMARY KEY (user_id, recipe_id)
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
                );
                """)

        self.conn.commit()

    # def write(self, item, overwrite=False):
    #     """Write a new object to the DB if its db_id is None. Otherwise edit existing object.
    #     Return db_id of the new object or number of affected rows if editing an existing one.

    #     :param overwrite: A bool. If False, existing objects will not be edited to prevent
    #         accidental changes to exisitng objects instead of creating new ones.
    #     """
    #     # if exisiting item is provided
    #     if item.db_id:
    #         if not overwrite:
    #             return 0

    #         d = {
    #             "IngredientCategory": lambda x: self.edit_ingredient_category(x.db_id, x.name),
    #             "Allergy"           : lambda x: self.edit_allergy(x.db_id, x.name),
    #             "Ingredient"        : lambda x: self.edit_ingredient(x.db_id,
    #                                                                  x.name,
    #                                                                  x.category.db_id,
    #                                                                  x.allergies),
    #             "Recipe"            : lambda x: self.edit_recipe(x.db_id, x.name, x.contents,
    #                                                              x.instructions),
    #             "User"              : lambda x: self.edit_user(x.db_id, x.name, x.password_hash,
    #                                                           x.allergies, x.meals, x.is_admin),
    #         }
    #         affected_rows = d[type(item).__name__](item)

    #         return affected_rows

    #     # if new item is provided
    #     d = {
    #         "IngredientCategory": lambda x: self.write_ingredient_category(x.name),
    #         "Allergy"           : lambda x: self.write_allergy(x.name),
    #         "Ingredient"        : lambda x: self.write_ingredient(x.name, x.category.db_id,
    #                                                      x.allergies),
    #         "Recipe"            : lambda x: self.write_recipe(x.name, x.contents, x.instructions),
    #         "User"              : lambda x: self.write_user(x.name, x.password_hash,
    #                                                      x.allergies, x.meals, x.is_admin),
    #     }
    #     item.db_id = d[type(item).__name__](item)

    #     return item.db_id



    # def write_user(self, name, password_hash, allergies=set(), meals=IdSet(), is_admin=False):
    #     """Write a new user to the DB. Return id of the new DB entry"""
    #     user = (name, password_hash, is_admin)
    #     self.c.execute("INSERT INTO users (name, password_hash, is_admin) VALUES (?, ?, ?)", user)

    #     self.c.execute("SELECT id FROM users WHERE name = ?", (name,))
    #     user_id = self.c.fetchone()["id"]

    #     user_allergies = set()
    #     for allergy in allergies:
    #         user_allergies.add((user_id, allergy.db_id))
    #     self.c.executemany("INSERT INTO user_allergies (user_id, allergy_id) VALUES (?, ?)",
    #                       user_allergies)

    #     user_meals = set()
    #     for recipe_id in meals:
    #         user_meals.add((user_id, recipe_id))
    #     self.c.executemany("INSERT INTO user_meals (user_id, recipe_id) VALUES (?, ?)",
    #                       user_meals)

    #     self.conn.commit()

    #     return user_id

    # def edit_user(self, db_id, new_name=None, new_password_hash=None, new_allergies=None, new_meals=None, new_is_admin=None):
    #     """Changes values of a user in the DB. Return number of rows affected.

    #     :param db_id: An integer. ID of the user in the DB.
    #     :param new_name: A string. New name of the user.
    #     :param new_password_hash: A string. New password hash of the user.
    #     :param new_allergies: A set of Allergy objects or allergy db_id integers.
    #     :param new_meals: A set of recipe db_id.
    #     Pass None to leave respective attributes without changes.
    #     """
    #     if not self.exists("users", db_id=db_id):
    #         return 0

    #     rows_affected = 0

    #     # Writing new name and/or password hash
    #     if new_name:
    #         t = (new_name, db_id)
    #         self.c.execute("UPDATE users SET name = ? WHERE id = ?", t)
    #         rows_affected += self.c.rowcount

    #     if new_password_hash:
    #         t = (new_password_hash, db_id)
    #         self.c.execute("UPDATE users SET password_hash = ? WHERE id = ?", t)
    #         rows_affected += self.c.rowcount

    #     if new_is_admin:
    #         t = (new_is_admin, db_id)
    #         self.c.execute("UPDATE users SET is_admin = ? WHERE id = ?", t)
    #         rows_affected += self.c.rowcount


    #     if not new_allergies == None:
    #         # Constructing sets of old and new allergy db_id of the user
    #         new_allergy_ids = set()
    #         for allergy in new_allergies:
    #             try:
    #                 new_allergy_id = int(allergy)
    #             except ValueError:
    #                 new_allergy_id = allergy.db_id
    #             new_allergy_ids.add(new_allergy_id)

    #         needle = (db_id,)
    #         rows = self.c.execute("SELECT allergy_id FROM user_allergies WHERE "
    #                                       "user_id = ?", needle).fetchall()
    #         old_allergy_ids = {x["allergy_id"] for x in rows}

    #         # Removing allergies missing in the new set and adding new ones missing in the old set
    #         for allergy_id in old_allergy_ids - new_allergy_ids:
    #             rows_affected += self.user_remove_allergy(db_id, allergy_id)
    #         for allergy_id in new_allergy_ids - old_allergy_ids:
    #             if self.user_add_allergy(db_id, allergy_id):
    #                 rows_affected += 1


    #     if not new_meals == None:
    #         # Constructing a set of old recipe db_id of the user
    #         needle = (db_id,)
    #         rows = self.c.execute("SELECT recipe_id FROM user_meals WHERE "
    #                                       "user_id = ?", needle).fetchall()
    #         old_recipe_ids = {x["recipe_id"] for x in rows}

    #         # Removing recipes missing in the new set and adding new ones missing in the old set
    #         for recipe_id in old_recipe_ids - new_meals:
    #             rows_affected += self.user_remove_meal(db_id, recipe_id)
    #         for recipe_id in new_meals - old_recipe_ids:
    #             if self.user_add_meal(db_id, recipe_id):
    #                 rows_affected += 1

    #     if rows_affected:
    #         self.conn.commit()
    #         return rows_affected

    #     return 0

    # def user_add_allergy(self, user_id, allergy_id, commit=False):
    #     """Add new allergy to a user in the DB. Return False if user is not found.

    #     :param user_id: An integer. ID of the user in the DB.
    #     :param allergy_id: An integer. ID of the allergy in the DB.
    #     :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
    #         if this method is called by methods with multiple transactions (e.g. edit_user)
    #         to avoid redundant commits or storing the object in an incomplete state.
    #     """
    #     if not self.exists("users", db_id=user_id):
    #         return False

    #     t = (user_id, allergy_id)
    #     self.c.execute("INSERT INTO user_allergies (user_id, allergy_id) VALUES (?, ?)", t)

    #     if commit:
    #         self.conn.commit()

    #     return True

    # def user_remove_allergy(self, user_id, allergy_id, commit=False):
    #     """Remove an allergy from a user in the DB. Return number of affected rows.

    #     :param user_id: An integer. ID of the user in the DB.
    #     :param allergy_id: An integer. ID of the allergy in the DB.
    #     :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
    #         if this method is called by methods with multiple transactions (e.g. edit_user)
    #         to avoid redundant commits or storing the object in an incomplete state.
    #     """

    #     needle = (user_id, allergy_id)
    #     self.c.execute("DELETE FROM user_allergies WHERE user_id  = ? AND allergy_id = ?", needle)
    #     rows_affected = self.c.rowcount

    #     if commit and rows_affected:
    #         self.conn.commit()

    #     return rows_affected

    # def user_add_meal(self, user_id, recipe_id, commit=False):
    #     """Add new meal to a user in the DB. Return False if user is not found.

    #     :param user_id: An integer. ID of the user in the DB.
    #     :param recipe_id: An integer. ID of the recipe in the DB.
    #     :param commit: A boolean. Method will only call DB's commit() if True. Should be avoided
    #         if this method is called by methods making multiple transactions (e.g. edit_user)
    #         to avoid redundant commits or storing the object in an incomplete state.
    #     """
    #     if not self.exists("users", db_id=user_id):
    #         return False

    #     t = (user_id, recipe_id)
    #     self.c.execute("INSERT INTO user_meals (user_id, recipe_id) VALUES (?, ?)", t)

    #     if commit:
    #         self.conn.commit()

    #     return True

    # def user_remove_meal(self, user_id, recipe_id, commit=False):
    #     """Remove a meal from a user in the DB. Return number of affected rows.

    #     :param user_id: An integer. ID of the user in the DB.
    #     :param recipe_id: An integer. ID of the recipe in the DB.
    #     :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
    #         if this method is called by methods with multiple transactions (e.g. edit_user)
    #         to avoid redundant commits or storing the object in an incomplete state.
    #     """

    #     needle = (user_id, recipe_id)
    #     self.c.execute("DELETE FROM user_meals WHERE user_id  = ? AND recipe_id = ?", needle)
    #     rows_affected = self.c.rowcount

    #     if commit and rows_affected:
    #         self.conn.commit()

    #     return rows_affected

    # def fetch_user_by_id(self, db_id):
    #     """Return a User object constructed with DB data based on provided db_id"""
    #     if not self.exists("users", id=db_id):
    #         return None

    #     needle = (db_id,)

    #     # Constructing allergies set
    #     self.c.execute("SELECT allergy_id FROM user_allergies WHERE user_id = ?", needle)
    #     rows = self.c.fetchall()
    #     allergies = set()
    #     for row in rows:
    #         allergies.add(self.fetch_allergy(row["allergy_id"]))

    #     # Constructing User object
    #     self.c.execute("SELECT * FROM users WHERE id = ?", needle)
    #     row = self.c.fetchone()
    #     if not row:
    #         return None
    #     user = User(row["name"], row["password_hash"], row["id"], allergies)

    #     return user

    # def fetch_user(self, db_id=None, **kwargs):
    #     """Return a User object. Must provide either of id, db_id or name argument"""
    #     if db_id:
    #         return self.fetch_user_by_id(db_id)
    #     if "id" in kwargs:
    #         return self.fetch_user_by_id(kwargs["id"])
    #     if "name" in kwargs:
    #         name = kwargs["name"]
    #         self.c.execute("SELECT id FROM users WHERE name = ?", (name,))
    #         row = self.c.fetchone()
    #         if row:
    #             db_id = row["id"]
    #             return self.fetch_user_by_id(db_id)

    #     return None

    # # DB object interpolation taken from Martijn Pieters's answer here:
    # # https://stackoverflow.com/a/25387570
    def exists(self, table_name, **search_params):
        """Ensure object exists in DB.

        :param table_name: A string. Name of the table were the object is to be located.
        :param search_params: kwargs where keys are column names. Values must be exact match,
            joined with AND in the SQL query.
        """

        objects = [to_db_obj_name(table_name)]
        needle = tuple()
        for key, value in search_params.items():
            objects.append(to_db_obj_name(key))
            needle += (value,)

        query = 'SELECT count(*) FROM "{}" WHERE "{}" = ?'
        query = query + ' AND "{}" = ?'*(len(needle) - 1)

        self.c.execute(query.format(*objects), needle)
        rows = self.c.fetchone()
        if not rows[0]:
            return False

        return True

    # def get_rows(self, table_name, order_by=None, **search_params):
    #     """Return all rows matching search critera in a table.

    #     :param table_name: A string. Name of the table were the object is to be located.
    #     :param order_by: A string. Must be name of the column and order type to order by e.g. 'name ASC'.
    #     :param search_params: kwargs where keys are column names. Values must be exact match,
    #         joined with AND in the SQL query.
    #     """
    #     try:
    #         search_params["id"] = search_params.pop("db_id")
    #     except KeyError:
    #         pass
    #     objects = [to_db_obj_name(table_name)]
    #     needle = tuple()
    #     for key, value in search_params.items():
    #         objects.append(to_db_obj_name(key))
    #         needle += (value,)

    #     query = 'SELECT * FROM "{}"'
    #     if search_params:
    #         query += ' WHERE "{}" = ?'
    #         query += ' AND "{}" = ?'*(len(needle) - 1)

    #     if order_by:
    #         query += " ORDER BY " + order_by

    #     self.c.execute(query.format(*objects), needle)
    #     rows = self.c.fetchall()

    #     return rows

    # def get_summary(self, obj_type, name_sort=False):
    #     """Return summary table for selected food object.
    #     Is an aggregating alias method. See individual methods for columns list.

    #     param obj_type: A string. Type of object for the summary. One of:
    #         ingredients
    #         ingredient_categories
    #         ingredients
    #         recipes
    #     param name_sort: A boolean. If True, summary will be recursively sorted by object name ascending.
    #     """
    #     d = {
    #         "allergies"            : lambda x: self.get_summary_allergies(x),
    #         "ingredient_categories": lambda x: self.get_summary_ingredient_categories(x),
    #         "ingredients"          : lambda x: self.get_summary_ingredients(x),
    #         "recipes"              : lambda x: self.get_summary_recipes(x),
    #     }

    #     return d[obj_type](name_sort)






# DB object interpolation taken from Martijn Pieters's answer here:
# https://stackoverflow.com/a/25387570
def to_db_obj_name(s):
    """Returns string modified so that it can be used as DB object (e.g table, column, etc.) name
    within double quotes of a query string.
    This method DOES NOT provide properly prevent injection and should only be used for internal values.
    """
    return s.replace('"', '""')
