import sqlite3

from backend.DBEntry import IngredientCategory, Allergy
from backend.Ingredient import Ingredient
from backend.Recipe import Recipe, Content
from backend.User import User, IdSet

DEFAULT_DB_PATH = "backend/food.db"

class DBHandler(object):
    """Handles storage and retrieval of within a DB.

    :param db_path: A string, path to the target DB.
    """
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.c = self.db.cursor()
        self.c.execute("PRAGMA foreign_keys = ON;")
        self.db.commit()

    def __del__(self):
        self.db.close()

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

                CREATE TABLE allergens(
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

        self.db.commit()

    def write(self, item, overwrite=False):
        """Write a new object to the DB if its db_id is None. Otherwise edit existing object.
        Return db_id of the new object or number of affected rows if editing an existing one.

        :param overwrite: A bool. If False, existing objects will not be edited to prevent
            accidental changes to exisitng objects instead of creating new ones.
        """
        # if exisiting item is provided
        if item.db_id:
            if not overwrite:
                return 0

            d = {
                "IngredientCategory": lambda x: self.edit_ingredient_category(x.db_id, x.name),
                "Allergy"           : lambda x: self.edit_allergy(x.db_id, x.name),
                "Ingredient"        : lambda x: self.edit_ingredient(x.db_id,
                                                                     x.name,
                                                                     x.category.db_id,
                                                                     x.allergies),
                "Recipe"            : lambda x: self.edit_recipe(x.db_id, x.name, x.contents,
                                                                 x.instructions),
                "User"              : lambda x: self.edit_user(x.db_id, x.name, x.password_hash,
                                                              x.allergies, x.meals, x.is_admin),
            }
            affected_rows = d[type(item).__name__](item)

            return affected_rows

        # if new item is provided
        d = {
            "IngredientCategory": lambda x: self.write_ingredient_category(x.name),
            "Allergy"           : lambda x: self.write_allergy(x.name),
            "Ingredient"        : lambda x: self.write_ingredient(x.name, x.category.db_id,
                                                         x.allergies),
            "Recipe"            : lambda x: self.write_recipe(x.name, x.contents, x.instructions),
            "User"              : lambda x: self.write_user(x.name, x.password_hash,
                                                         x.allergies, x.meals, x.is_admin),
        }
        item.db_id = d[type(item).__name__](item)

        return item.db_id

    def write_ingredient_category(self, name):
        """Write a new ingredient category to the DB. Return id of the new DB entry"""
        category = (name,)
        self.c.execute("INSERT INTO ingredient_categories (name) VALUES (?)", category)
        self.c.execute("SELECT id FROM ingredient_categories WHERE name = ?", category)

        self.db.commit()

        return self.c.fetchone()["id"]

    def edit_ingredient_category(self, db_id, new_name):
        """Changes values of an ingredient category in the DB. Return number of rows affected"""
        if not self.exists("ingredient_categories", db_id=db_id):
            return 0

        t = (new_name, db_id)
        self.c.execute("UPDATE ingredient_categories SET name = ? WHERE id = ?", t)
        if self.c.rowcount:
            self.db.commit()
            return self.c.rowcount

        return 0

    def write_allergy(self, name):
        """Write a new allergy to the DB. Return id of the new DB entry"""
        allergy = (name,)
        self.c.execute("INSERT INTO allergies (name) VALUES (?)", allergy)
        self.c.execute("SELECT id FROM allergies WHERE name = ?", allergy)

        self.db.commit()

        return self.c.fetchone()["id"]

    def edit_allergy(self, db_id, new_name):
        """Changes values of an allergy in the DB. Return number of rows affected"""
        if not self.exists("allergies", db_id=db_id):
            return 0

        t = (new_name, db_id)
        self.c.execute("UPDATE allergies SET name = ? WHERE id = ?", t)
        if self.c.rowcount:
            self.db.commit()
            return self.c.rowcount

        return 0

    def write_ingredient(self, name, category_id, allergies=set()):
        """Write a new ingredient to the DB. Return id of the new DB entry"""
        ingredient = (name, category_id)
        self.c.execute("INSERT INTO ingredients (name, category_id) VALUES (?, ?)", ingredient)

        self.c.execute("SELECT id FROM ingredients WHERE name = ?", (name,))
        ingredient_id = self.c.fetchone()["id"]

        allergens = set()
        for allergy in allergies:
            allergens.add((ingredient_id, allergy.db_id))
        self.c.executemany("INSERT INTO allergens (ingredient_id, allergy_id) VALUES (?, ?)",
                           allergens)

        self.db.commit()

        return ingredient_id

    def edit_ingredient(self, db_id, new_name=None, new_category=None, new_allergies=None):
        """Changes values of an ingredient in the DB. Return number of rows affected.

        :param new_name: A string. New name of the ingredient.
        :param new_category: IngredientCategory object or ingredient category db_id.
        :param new_allergies: A set of Allergy objects or allergy db_id integers.
        Pass None to leave respective attributes without changes.
        """
        if not self.exists("ingredients", db_id=db_id):
            return 0

        rows_affected = 0

        # Writing new name and/or category
        if new_name:
            t = (new_name, db_id)
            self.c.execute("UPDATE ingredients SET name = ? WHERE id = ?", t)
            rows_affected += self.c.rowcount

        if new_category:
            try:
                new_category_id = int(new_category)
            except ValueError:
                new_category_id = new_category.db_id

            t = (new_category_id, db_id)
            self.c.execute("UPDATE ingredients SET category_id = ? WHERE id = ?", t)
            rows_affected += self.c.rowcount

        if not new_allergies == None:
            # Constructing sets of old and new allergy db_id of the ingredient
            new_allergy_ids = set()
            for allergy in new_allergies:
                try:
                    new_allergy_id = int(allergy)
                except:
                    new_allergy_id = allergy.db_id
                new_allergy_ids.add(new_allergy_id)

            needle = (db_id,)
            old_allergies = self.c.execute("SELECT allergy_id FROM allergens WHERE "
                                           "ingredient_id = ?", needle).fetchall()
            old_allergy_ids = {x["allergy_id"] for x in old_allergies}

            # Removing allergies missing in the new set and adding new ones missing in the old set
            for allergy_id in old_allergy_ids - new_allergy_ids:
                rows_affected += self.ingredient_remove_allergy(db_id, allergy_id)
            for allergy_id in new_allergy_ids - old_allergy_ids:
                if self.ingredient_add_allergy(db_id, allergy_id):
                    rows_affected += 1

        if rows_affected:
            self.db.commit()
            return rows_affected

        return 0

    def ingredient_add_allergy(self, ingredient_id, allergy_id, commit=False):
        """Add new allergy to an ingredient in the DB. Return False if ingredient is not found.

        :param ingredient_id: An integer. ID of the ingredient in the DB.
        :param allergy_id: An integer. ID of the allergy in the DB.
        :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods with multiple transactions (e.g. edit_ingredient)
            to avoid redundant commits or storing the object in an incomplete state.
        """
        if not self.exists("ingredients", db_id=ingredient_id):
            return False

        t = (ingredient_id, allergy_id)
        self.c.execute("INSERT INTO allergens (ingredient_id, allergy_id) VALUES (?, ?)", t)

        if commit:
            self.db.commit()

        return True

    def ingredient_remove_allergy(self, ingredient_id, allergy_id, commit=False):
        """Remove an allergy from an ingredient in the DB. Return number of affected rows.

        :param ingredient_id: An integer. ID of the ingredient in the DB.
        :param allergy_id: An integer. ID of the allergy in the DB.
        :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods with multiple transactions (e.g. edit_ingredient)
            to avoid redundant commits or storing the object in an incomplete state.
        """

        needle = (ingredient_id, allergy_id)
        self.c.execute("DELETE FROM allergens WHERE ingredient_id = ? AND allergy_id = ?", needle)
        rows_affected = self.c.rowcount

        if commit and rows_affected:
            self.db.commit()

        return rows_affected

    def write_recipe(self, name, contents, instructions):
        """Write a new recipe to the DB. Return id of the new DB entry"""
        recipe = (name, instructions)
        self.c.execute("INSERT INTO recipes (name, instructions) VALUES (?, ?)", recipe)

        self.c.execute("SELECT id FROM recipes WHERE name = ?", (name,))
        recipe_id = self.c.fetchone()["id"]

        content_set = set()
        for c in contents:
            content_set.add((recipe_id, c.ingredient.db_id, c.amount,
                             c.units))
        self.c.executemany("INSERT INTO recipe_contents (recipe_id, ingredient_id, amount, "
                           "units) VALUES (?, ?, ?, ?)", content_set)

        self.db.commit()

        return recipe_id

    def edit_recipe(self, db_id, new_name=None, new_contents=None, new_instructions=None):
        """Changes values of a recipe in the DB. Return number of rows affected.

        :param new_name: A string. New name of the recipe.
        :param new_contents: A set of Content objects.
        :param new_instructions: A string. New instructions text.
        Pass None to leave respective attributes without changes.
        """
        if not self.exists("recipes", db_id=db_id):
            return 0

        rows_affected = 0

        # Writing new name and/or instructions
        if new_name:
            t = (new_name, db_id)
            self.c.execute("UPDATE recipes SET name = ? WHERE id = ?", t)
            rows_affected += self.c.rowcount

        if new_instructions:
            t = (new_instructions, db_id)
            self.c.execute("UPDATE recipes SET instructions = ? WHERE id = ?", t)
            rows_affected += self.c.rowcount


        if not new_contents == None:
            # Constructing sets of old and new contents' ingredient db_id
            new_ingredient_ids = {x.ingredient.db_id for x in new_contents}

            needle = (db_id,)
            old_contents = self.c.execute("SELECT ingredient_id FROM recipe_contents "
                                          "WHERE recipe_id = ?", needle).fetchall()
            old_ingredient_ids = {x["ingredient_id"] for x in old_contents}

            # Removing contents missing in the new set
            for ingredient_id in old_ingredient_ids - new_ingredient_ids:
                rows_affected += self.recipe_remove_content(db_id, ingredient_id)

            # Adding contents missing in the old set
            missing_contents = {x for x in new_contents
                                if x.ingredient.db_id in (new_ingredient_ids - old_ingredient_ids)}
            for c in missing_contents:
                if self.recipe_add_content(db_id, c.ingredient.db_id, c.amount, c.units):
                    rows_affected += 1

            # Updating values of contents present in the old and new set
            missing_contents = {x for x in new_contents
                                if x.ingredient.db_id in (old_ingredient_ids & new_ingredient_ids)}
            for c in missing_contents:
                if self.recipe_edit_content(db_id, c.ingredient.db_id, c.amount, c.units):
                    rows_affected += 1


        if rows_affected:
            self.db.commit()
            return rows_affected

        return 0

    def recipe_add_content(self, recipe_id, ingredient_id, amount, units=None, commit=False):
        """Add new content to a recipe in the DB. Return False if recipe is not found.

        :param recipe_id: An integer. ID of the recipe in the DB.
        :param ingredient_id: An integer. ID of the ingredient in the DB.
        :param amount: An integer. Amount of the ingredient in the DB.
        :param units: An string. Represents units of measurement used for amount. Use None for
            quantifiable ingredients.
        :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods with multiple transactions (e.g. edit_recipe)
            to avoid redundant commits or storing the object in an incomplete state.
        """
        if not self.exists("recipes", db_id=recipe_id):
            return False

        t = (recipe_id, ingredient_id, amount, units)
        self.c.execute("INSERT INTO recipe_contents (recipe_id, ingredient_id, amount, units) "
                       "VALUES (?, ?, ?, ?)", t)

        if commit:
            self.db.commit()

        return True

    def recipe_remove_content(self, recipe_id, ingredient_id, commit=False):
        """Remove a content from a recipe in the DB. Return number of affected rows.

        :param recipe_id: An integer. ID of the recipe in the DB.
        :param ingredient_id: An integer. ID of the ingredient in the DB.
        :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods with multiple transactions (e.g. edit_recipe)
            to avoid redundant commits or storing the object in an incomplete state.
        """
        needle = (recipe_id, ingredient_id)
        self.c.execute("DELETE FROM recipe_contents WHERE recipe_id = ? AND ingredient_id = ?",
                       needle)
        rows_affected = self.c.rowcount

        if commit and rows_affected:
            self.db.commit()

        return rows_affected

    def recipe_edit_content(self, recipe_id, ingredient_id, amount, units=None, commit=None):
        """Edit a content in a recipe in the DB. Return False if recipe is not found.

        :param recipe_id: An integer. ID of the recipe in the DB.
        :param ingredient_id: An integer. ID of the ingredient in the DB.
        :param amount: An integer. Amount of the ingredient in the DB.
        :param units: An string. Represents units of measurement used for amount. Use None for
            quantifiable ingredients.
        :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods with multiple transactions (e.g. edit_recipe)
            to avoid redundant commits or storing the object in an incomplete state.
        """
        t = (amount, units, recipe_id, ingredient_id)
        self.c.execute("UPDATE recipe_contents SET amount = ?, units = ? "
                       "WHERE recipe_id = ? AND ingredient_id = ?", t)
        rows_affected = self.c.rowcount

        if commit and rows_affected:
            self.db.commit()

        return rows_affected

    def write_user(self, name, password_hash, allergies=set(), meals=IdSet(), is_admin=False):
        """Write a new user to the DB. Return id of the new DB entry"""
        user = (name, password_hash, is_admin)
        self.c.execute("INSERT INTO users (name, password_hash, is_admin) VALUES (?, ?, ?)", user)

        self.c.execute("SELECT id FROM users WHERE name = ?", (name,))
        user_id = self.c.fetchone()["id"]

        user_allergies = set()
        for allergy in allergies:
            user_allergies.add((user_id, allergy.db_id))
        self.c.executemany("INSERT INTO user_allergies (user_id, allergy_id) VALUES (?, ?)",
                           user_allergies)

        user_meals = set()
        for recipe_id in meals:
            user_meals.add((user_id, recipe_id))
        self.c.executemany("INSERT INTO user_meals (user_id, recipe_id) VALUES (?, ?)",
                           user_meals)

        self.db.commit()

        return user_id

    def edit_user(self, db_id, new_name=None, new_password_hash=None, new_allergies=None, new_meals=None, new_is_admin=None):
        """Changes values of a user in the DB. Return number of rows affected.

        :param db_id: An integer. ID of the user in the DB.
        :param new_name: A string. New name of the user.
        :param new_password_hash: A string. New password hash of the user.
        :param new_allergies: A set of Allergy objects or allergy db_id integers.
        :param new_meals: A set of recipe db_id.
        Pass None to leave respective attributes without changes.
        """
        if not self.exists("users", db_id=db_id):
            return 0

        rows_affected = 0

        # Writing new name and/or password hash
        if new_name:
            t = (new_name, db_id)
            self.c.execute("UPDATE users SET name = ? WHERE id = ?", t)
            rows_affected += self.c.rowcount

        if new_password_hash:
            t = (new_password_hash, db_id)
            self.c.execute("UPDATE users SET password_hash = ? WHERE id = ?", t)
            rows_affected += self.c.rowcount

        if new_is_admin:
            t = (new_is_admin, db_id)
            self.c.execute("UPDATE users SET is_admin = ? WHERE id = ?", t)
            rows_affected += self.c.rowcount


        if not new_allergies == None:
            # Constructing sets of old and new allergy db_id of the user
            new_allergy_ids = set()
            for allergy in new_allergies:
                try:
                    new_allergy_id = int(allergy)
                except:
                    new_allergy_id = allergy.db_id
                new_allergy_ids.add(new_allergy_id)

            needle = (db_id,)
            rows = self.c.execute("SELECT allergy_id FROM user_allergies WHERE "
                                           "user_id = ?", needle).fetchall()
            old_allergy_ids = {x["allergy_id"] for x in rows}

            # Removing allergies missing in the new set and adding new ones missing in the old set
            for allergy_id in old_allergy_ids - new_allergy_ids:
                rows_affected += self.user_remove_allergy(db_id, allergy_id)
            for allergy_id in new_allergy_ids - old_allergy_ids:
                if self.user_add_allergy(db_id, allergy_id):
                    rows_affected += 1


        if not new_meals == None:
            # Constructing a set of old recipe db_id of the user
            needle = (db_id,)
            rows = self.c.execute("SELECT recipe_id FROM user_meals WHERE "
                                           "user_id = ?", needle).fetchall()
            old_recipe_ids = {x["recipe_id"] for x in rows}

            # Removing recipes missing in the new set and adding new ones missing in the old set
            for recipe_id in old_recipe_ids - new_meals:
                rows_affected += self.user_remove_meal(db_id, recipe_id)
            for recipe_id in new_meals - old_recipe_ids:
                if self.user_add_meal(db_id, recipe_id):
                    rows_affected += 1

        if rows_affected:
            self.db.commit()
            return rows_affected

        return 0

    def user_add_allergy(self, user_id, allergy_id, commit=False):
        """Add new allergy to a user in the DB. Return False if user is not found.

        :param user_id: An integer. ID of the user in the DB.
        :param allergy_id: An integer. ID of the allergy in the DB.
        :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods with multiple transactions (e.g. edit_user)
            to avoid redundant commits or storing the object in an incomplete state.
        """
        if not self.exists("users", db_id=user_id):
            return False

        t = (user_id, allergy_id)
        self.c.execute("INSERT INTO user_allergies (user_id, allergy_id) VALUES (?, ?)", t)

        if commit:
            self.db.commit()

        return True

    def user_remove_allergy(self, user_id, allergy_id, commit=False):
        """Remove an allergy from a user in the DB. Return number of affected rows.

        :param user_id: An integer. ID of the user in the DB.
        :param allergy_id: An integer. ID of the allergy in the DB.
        :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods with multiple transactions (e.g. edit_user)
            to avoid redundant commits or storing the object in an incomplete state.
        """

        needle = (user_id, allergy_id)
        self.c.execute("DELETE FROM user_allergies WHERE user_id  = ? AND allergy_id = ?", needle)
        rows_affected = self.c.rowcount

        if commit and rows_affected:
            self.db.commit()

        return rows_affected

    def user_add_meal(self, user_id, recipe_id, commit=False):
        """Add new meal to a user in the DB. Return False if user is not found.

        :param user_id: An integer. ID of the user in the DB.
        :param recipe_id: An integer. ID of the recipe in the DB.
        :param commit: A boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods making multiple transactions (e.g. edit_user)
            to avoid redundant commits or storing the object in an incomplete state.
        """
        if not self.exists("users", db_id=user_id):
            return False

        t = (user_id, recipe_id)
        self.c.execute("INSERT INTO user_meals (user_id, recipe_id) VALUES (?, ?)", t)

        if commit:
            self.db.commit()

        return True

    def user_remove_meal(self, user_id, recipe_id, commit=False):
        """Remove a meal from a user in the DB. Return number of affected rows.

        :param user_id: An integer. ID of the user in the DB.
        :param recipe_id: An integer. ID of the recipe in the DB.
        :param commit: A Boolean. Method will only call DB's commit() if True. Should be avoided
            if this method is called by methods with multiple transactions (e.g. edit_user)
            to avoid redundant commits or storing the object in an incomplete state.
        """

        needle = (user_id, recipe_id)
        self.c.execute("DELETE FROM user_meals WHERE user_id  = ? AND recipe_id = ?", needle)
        rows_affected = self.c.rowcount

        if commit and rows_affected:
            self.db.commit()

        return rows_affected

    def fetch_ingredient_category(self, db_id):
        """Return an IngredientCategory object constructed with DB data based on provided db_id"""
        if not self.exists("ingredient_categories", id=db_id):
            return None

        needle = (db_id,)
        self.c.execute("SELECT id, name FROM ingredient_categories WHERE id = ?", needle)
        row = self.c.fetchone()
        category = IngredientCategory(row["name"], row["id"])

        return category

    def fetch_allergy(self, db_id):
        """Return an Allergy object constructed with DB data based on provided db_id"""
        if not self.exists("allergies", id=db_id):
            return None

        needle = (db_id,)
        self.c.execute("SELECT id, name FROM allergies WHERE id = ?", needle)
        row = self.c.fetchone()
        allergy = Allergy(row["name"], row["id"])

        return allergy

    def fetch_ingredient(self, db_id):
        """Return an Ingredient object constructed with DB data based on provided db_id"""
        if not self.exists("ingredients", id=db_id):
            return None

        needle = (db_id,)

        # Constructing allergies set
        self.c.execute("SELECT allergy_id FROM allergens WHERE ingredient_id = ?", needle)
        rows = self.c.fetchall()
        allergies = set()
        for row in rows:
            allergies.add(self.fetch_allergy(row["allergy_id"]))

        # Constructing Ingredient object
        self.c.execute("SELECT * FROM ingredients WHERE id = ?", needle)
        row = self.c.fetchone()
        if not row:
            return None
        category = self.fetch_ingredient_category(row["category_id"])
        ingredient = Ingredient(row["name"], category, row["id"], allergies)

        return ingredient

    def fetch_recipe(self, db_id):
        """Return a Recipe object constructed with DB data based on provided db_id"""
        if not self.exists("recipes", id=db_id):
            return None

        # Constructing contents set
        needle = (db_id,)
        self.c.execute("SELECT ingredient_id, amount, units FROM recipe_contents "
                       "WHERE recipe_id = ?", needle)
        rows = self.c.fetchall()
        contents = set()
        for row in rows:
            ingredient = self.fetch_ingredient(row["ingredient_id"])
            content = Content(ingredient, row["amount"], row["units"])
            contents.add(content)

        # Constructing the Recipe object
        self.c.execute("SELECT * FROM recipes WHERE id = ?", needle)
        row = self.c.fetchone()
        recipe = Recipe(row["name"], row["id"], contents, row["instructions"])

        return recipe

    def fetch_user_by_id(self, db_id):
        """Return a User object constructed with DB data based on provided db_id"""
        if not self.exists("users", id=db_id):
            return None

        needle = (db_id,)

        # Constructing allergies set
        self.c.execute("SELECT allergy_id FROM user_allergies WHERE user_id = ?", needle)
        rows = self.c.fetchall()
        allergies = set()
        for row in rows:
            allergies.add(self.fetch_allergy(row["allergy_id"]))

        # Constructing User object
        self.c.execute("SELECT * FROM users WHERE id = ?", needle)
        row = self.c.fetchone()
        if not row:
            return None
        user = User(row["name"], row["password_hash"], row["id"], allergies)

        return user

    def fetch_user(self, db_id=None, **kwargs):
        """Return a User object. Must provide either of id, db_id or name argument"""
        if db_id:
            return self.fetch_user_by_id(db_id)
        if "id" in kwargs:
            return self.fetch_user_by_id(kwargs["id"])
        if "name" in kwargs:
            name = kwargs["name"]
            self.c.execute("SELECT id FROM users WHERE name = ?", (name,))
            row = self.c.fetchone()
            if row:
                db_id = row["id"]
                return self.fetch_user_by_id(db_id)

        return None

    # DB object interpolation taken from Martijn Pieters's answer here:
    # https://stackoverflow.com/a/25387570
    def exists(self, table_name, **search_params):
        """Ensure object exists in DB.

        :param table_name: A string. Name of the table were the object is to be located.
        :param search_params: kwargs where keys are column names. Values must be exact match,
            joined with AND in the SQL query.
        """
        try:
            search_params["id"] = search_params.pop("db_id")
        except KeyError:
            pass
        objects = [table_name.replace('"', '""')]
        needle = tuple()
        for key, value in search_params.items():
            objects.append(key.replace('"', '""'))
            needle += (value,)

        query = 'SELECT count(*) FROM "{}" WHERE "{}" = ?'
        query = query + ' AND "{}" = ?'*(len(needle) - 1)

        self.c.execute(query.format(*objects), needle)
        rows = self.c.fetchone()
        if not rows[0]:
            return False

        return True

    def get_rows(self, table_name, order_by=None, **search_params):
        """Return all rows matching search critera in a table.

        :param table_name: A string. Name of the table were the object is to be located.
        :param order_by: A string. Must be name of the column and order type to order by e.g. 'name ASC'.
        :param search_params: kwargs where keys are column names. Values must be exact match,
            joined with AND in the SQL query.
        """
        try:
            search_params["id"] = search_params.pop("db_id")
        except KeyError:
            pass
        objects = [table_name.replace('"', '""')]
        needle = tuple()
        for key, value in search_params.items():
            objects.append(key.replace('"', '""'))
            needle += (value,)

        query = 'SELECT * FROM "{}"'
        if search_params:
            query += ' WHERE "{}" = ?'
            query += ' AND "{}" = ?'*(len(needle) - 1)

        if order_by:
            query += " ORDER BY " + order_by

        self.c.execute(query.format(*objects), needle)
        rows = self.c.fetchall()

        return rows

    def get_summary(self, obj_type, name_sort=False):
        """Return summary table for selected food object.
        Is an aggregating alias method. See individual methods for columns list.

        param obj_type: A string. Type of object for the summary. One of:
            ingredients
            ingredient_categories
            ingredients
            recipes
        param name_sort: A boolean. If True, summary will be recursively sorted by object name ascending.
        """
        d = {
            "allergies"            : lambda x: self.get_summary_allergies(x),
            "ingredient_categories": lambda x: self.get_summary_ingredient_categories(x),
            "ingredients"          : lambda x: self.get_summary_ingredients(x),
            "recipes"              : lambda x: self.get_summary_recipes(x),
        }

        return d[obj_type](name_sort)

    def get_summary_allergies(self, name_sort=False):
        """Return summary table for Allergy entries with columns:
        id: allergy db_id.
        name: allergy name.
        dependents: number of objects with this allergy - ingredients and users.

        param name_sort: A boolean. If True, summary will be recursively sorted by object name ascending.
        """
        self.c.execute("SELECT id, name, "
                       "  (COUNT(ingredient_id) + COUNT(user_id)) as dependents "
                       "FROM allergies "
                       "LEFT JOIN allergens "
                       "  ON allergies.id = allergens.allergy_id "
                       "LEFT JOIN user_allergies "
                       "  ON allergies.id = user_allergies.allergy_id "
                       "GROUP BY allergies.id "
                       "ORDER BY allergies.name ASC"\
                       )
        rows = self.c.fetchall()

        if name_sort:
            rows.sort(key=lambda x: x["name"].lower())


        return rows

    def get_summary_ingredient_categories(self, name_sort=False):
        """Return summary table for IngredientCategory entries with columns:
        id: category db_id.
        name: category name.
        dependents: number of objects with this category - ingredients.

        param name_sort: A boolean. If True, summary will be recursively sorted by object name ascending.
        """
        self.c.execute("SELECT ingredient_categories.id, ingredient_categories.name, "
                       "  COUNT(ingredients.id) as dependents "
                       "FROM ingredient_categories "
                       "LEFT JOIN ingredients "
                       "  ON ingredient_categories.id = ingredients.category_id "
                       "GROUP BY ingredient_categories.id "
                       "ORDER BY ingredient_categories.name ASC"
                       )
        rows = self.c.fetchall()

        if name_sort:
            rows.sort(key=lambda x: x["name"].lower())

        return rows

    def get_summary_ingredients(self, name_sort=False):
        """Return summary table for Ingredient entries with columns:
        id: ingredient db_id.
        name: ingredient name.
        category: ingredient category name.
        allergies: list of allergies.
        dependents: number of objects with this category - recipe contents.

        param name_sort: A boolean. If True, summary will be recursively sorted by object name ascending.
        """
        rows = []

        # Get id, name and category of ingredients
        self.c.execute("SELECT ingredients.id, ingredients.name, "
                       "  ingredient_categories.name as category "
                       "FROM ingredients "
                       "LEFT JOIN ingredient_categories "
                       "  ON ingredients.category_id = ingredient_categories.id "
                       "ORDER BY ingredients.id ASC"
        )
        for db_row in self.c.fetchall():
            row = {}
            for key, value in zip(db_row.keys(), db_row):
                row[key] = value
            rows.append(row)


        # Get allergy lists
        self.c.execute("SELECT allergens.ingredient_id, allergies.name as allergy_name "
                       "FROM allergens "
                       "LEFT JOIN allergies "
                       "  ON allergens.allergy_id = allergies.id "
                       "ORDER BY allergens.ingredient_id ASC"
                       )
        it_rows = iter(rows)
        row = next(it_rows)
        for db_row in self.c.fetchall():
            while not db_row["ingredient_id"] == row["id"]:
                # Ensure at least an empty 'cell' exists for this ingredient before moving to next
                try:
                    row["allergies"]
                except KeyError:
                    row["allergies"] = []
                row = next(it_rows)

            try:
                row["allergies"].append(db_row["allergy_name"])
            except:
                row["allergies"] = [db_row["allergy_name"]]

        # Fill remaining rows with empty allergy lists
        finished = False
        while not finished:
            try:
                row = next(it_rows)
                row["allergies"] = []
            except StopIteration:
                finished = True


        # Get dependents
        self.c.execute("SELECT ingredient_id, COUNT(recipe_id) as dependents FROM recipe_contents "
                       "GROUP BY ingredient_id "
                       "ORDER BY ingredient_id ASC"
                       )
        it_rows = iter(rows)
        row = next(it_rows)
        for db_row in self.c.fetchall():
            while not db_row["ingredient_id"] == row["id"]:
                # Set dependents = 0 for ingredients that don't exist in recipe_contents table
                try:
                    row["dependents"]
                except KeyError:
                    row["dependents"] = 0

                row = next(it_rows)

            row["dependents"] = db_row["dependents"]

        # Fill remaining rows with dependents = 0
        finished = False
        while not finished:
            try:
                row = next(it_rows)
                row["dependents"] = 0
            except StopIteration:
                finished = True


        if name_sort:
            rows.sort(key=lambda x: x["name"].lower())
            for row in rows:
                row["allergies"].sort(key=str.lower)


        return rows

    def get_summary_recipes(self, name_sort=False):
        """Return summary table for Recipe entries with columns:
        id: recipe db_id.
        name: recipe name.
        instructions: instructions on how to prepare the dish.
        contents: string listing ingredients and their amounts.

        param name_sort: A boolean. If True, summary will be recursively sorted by object name ascending.
        """
        rows = []

        # Get id, name and category of ingredients
        self.c.execute("SELECT id, name, instructions "
                       "FROM recipes "
                       "ORDER BY id ASC"
        )
        for db_row in self.c.fetchall():
            row = {}
            for key, value in zip(db_row.keys(), db_row):
                row[key] = value
            rows.append(row)


        # Get content lists
        self.c.execute("SELECT recipe_contents.recipe_id, ingredients.name as ingredient, "
                       "  recipe_contents.amount, recipe_contents.units "
                       "FROM recipe_contents "
                       "LEFT JOIN ingredients "
                       "  ON recipe_contents.ingredient_id = ingredients.id "
                       "ORDER BY recipe_id ASC"
                       )
        it_rows = iter(rows)
        row = next(it_rows)
        for db_row in self.c.fetchall():
            while not db_row["recipe_id"] == row["id"]:
                # Ensure at least an empty 'cell' exists for this recipe before moving to next
                try:
                    row["contents"]
                except KeyError:
                    row["contents"] = []
                row = next(it_rows)

            content = {
                "ingredient": db_row["ingredient"],
                "amount"    : db_row["amount"],
                "units"     : db_row["units"],
            }
            try:
                row["contents"].append(content)
            except KeyError:
                row["contents"] = [content]

        # Fill remaining rows with empty content lists
        finished = False
        while not finished:
            try:
                row = next(it_rows)
                row["contents"] = []
            except StopIteration:
                finished = True

        if name_sort:
            rows.sort(key=lambda x: x["name"].lower())
            for row in rows:
                row["contents"].sort(key=lambda x: x["ingredient"].lower())


        return rows
