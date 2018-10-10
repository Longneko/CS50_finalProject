import sqlite3

from backend.DBEntry import IngredientCategory, Allergy
from backend.Ingredient import Ingredient
from backend.Recipe import Recipe, Content
from backend.User import User

DEFAULT_DB_PATH = "backend/food.db"

class DBHandler(object):
    """Handles storage and retrieval of within a DB.

    :param db_path: A string, path to the target DB.
    """
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.c = self.db.cursor()
        self.c.execute("PRAGMA foreign_keys = ON;")
        self.db.commit()

    def __del__(self):
        self.db.close()

    def create_schema(self):
        """Creates the required schema in an empty DB"""
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
                  allergy_id INTEGER NOT NULL,
                  ingredient_id INTEGER NOT NULL,
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
                  units INTEGER NOT NULL,
                  unit_type TEXT DEFAULT NULL,
                  PRIMARY KEY (recipe_id, ingredient_id),
                  FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                  FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
                );

                CREATE TABLE users(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE,
                  password_hash TEXT NOT NULL
                );

                CREATE TABLE user_allergies(
                  allergy_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  PRIMARY KEY (allergy_id, user_id),
                  FOREIGN KEY (allergy_id) REFERENCES allergies(id),
                  FOREIGN KEY (user_id) REFERENCES users(id)
                );
                """)

        self.db.commit()

    def write(self, item):
        d = {
            "IngredientCategory": lambda x: self.write_ingredient_category(x.name),
            "Allergy"           : lambda x: self.write_allergy(x.name),
            "Ingredient"        : lambda x: self.write_ingredient(x.name, x.category.db_id,
                                                         x.allergies),
            "Recipe"            : lambda x: self.write_recipe(x.name, x.contents, x.instructions),
            "User"              : lambda x: self.write_user(x.name, x.password_hash,
                                                         x.allergies),
        }
        item.db_id = d[type(item).__name__](item)

        return item.db_id

    def write_ingredient_category(self, name):
        """Writes a new ingredient category to the DB. Returns id of the new DB entry"""
        category = (name,)
        self.c.execute("INSERT INTO ingredient_categories (name) VALUES (?)", category)
        self.c.execute("SELECT id FROM ingredient_categories WHERE name = ?", category)

        self.db.commit()

        return self.c.fetchone()["id"]

    def write_allergy(self, name):
        """Writes a new ingredient category to the DB. Returns id of the new DB entry"""
        allergy = (name,)
        self.c.execute("INSERT INTO allergies (name) VALUES (?)", allergy)
        self.c.execute("SELECT id FROM allergies WHERE name = ?", allergy)

        self.db.commit()

        return self.c.fetchone()["id"]

    def write_ingredient(self, name, category_id, allergies=set()):
        """Writes a new ingredient to the DB. Returns id of the new DB entry"""
        ingredient = (name, category_id)
        self.c.execute("INSERT INTO ingredients (name, category_id) VALUES (?, ?)", ingredient)

        self.c.execute("SELECT id FROM ingredients WHERE name = ?", (name,))
        ingredient_id = self.c.fetchone()["id"]

        allergens = set()
        for allergy in allergies:
            allergens.add((allergy.db_id, ingredient_id))
        self.c.executemany("INSERT INTO allergens (allergy_id, ingredient_id) VALUES (?, ?)",
                           allergens)

        self.db.commit()

        return ingredient_id

    def write_recipe(self, name, contents, instructions):
        """Writes a new recipe to the DB. Returns id of the new DB entry"""
        recipe = (name, instructions)
        self.c.execute("INSERT INTO recipes (name, instructions) VALUES (?, ?)", recipe)

        self.c.execute("SELECT id FROM recipes WHERE name = ?", (name,))
        recipe_id = self.c.fetchone()["id"]

        content_set = set()
        for content in contents:
            content_set.add((recipe_id, content.ingredient.db_id, content.units,
                             content.unit_type))
        self.c.executemany("INSERT INTO recipe_contents (recipe_id, ingredient_id, units, "
                           "unit_type) VALUES (?, ?, ?, ?)", content_set)

        self.db.commit()

        return recipe_id

    def write_user(self, name, password_hash, allergies=set()):
        """Writes a new user to the DB. Returns id of the new DB entry"""
        user = (name, password_hash)
        self.c.execute("INSERT INTO users (name, password_hash) VALUES (?, ?)", user)

        self.c.execute("SELECT id FROM users WHERE name = ?", (name,))
        user_id = self.c.fetchone()["id"]

        user_allergies = set()
        for allergy in allergies:
            user_allergies.add((allergy.db_id, user_id))
        self.c.executemany("INSERT INTO user_allergies (allergy_id, user_id) VALUES (?, ?)",
                           user_allergies)

        self.db.commit()

        return user_id

    def fetch_ingredient_category(self, db_id):
        """Returns an IngredientCategory object constructed with DB data based on provided db_id"""
        if not self.exists("ingredient_categories", id=db_id):
            return None

        needle = (db_id,)
        self.c.execute("SELECT id, name FROM ingredient_categories WHERE id = ?", needle)
        row = self.c.fetchone()
        category = IngredientCategory(row["name"], row["id"])

        return category

    def fetch_allergy(self, db_id):
        """Returns an Allergy object constructed with DB data based on provided db_id"""
        if not self.exists("allergies", id=db_id):
            return None

        needle = (db_id,)
        self.c.execute("SELECT id, name FROM allergies WHERE id = ?", needle)
        row = self.c.fetchone()
        allergy = Allergy(row["name"], row["id"])

        return allergy

    def fetch_ingredient(self, db_id):
        """Returns an Ingredient object constructed with DB data based on provided db_id"""
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
        """Returns a Recipe object constructed with DB data based on provided db_id"""
        if not self.exists("recipes", id=db_id):
            return None

        # Constructing contents set
        needle = (db_id,)
        self.c.execute("SELECT ingredient_id, units, unit_type FROM recipe_contents "
                       "WHERE recipe_id = ?", needle)
        rows = self.c.fetchall()
        contents = set()
        for row in rows:
            ingredient = self.fetch_ingredient(row["ingredient_id"])
            content = Content(ingredient, row["units"], row["unit_type"])
            contents.add(content)

        # Constructing the Recipe object
        self.c.execute("SELECT * FROM recipes WHERE id = ?", needle)
        row = self.c.fetchone()
        recipe = Recipe(row["name"], row["id"], contents, row["instructions"])

        return recipe

    def fetch_user(self, db_id):
        """Returns a User object constructed with DB data based on provided db_id"""
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

    # DB object interpolation taken from Martijn Pieters's answer here:
    # https://stackoverflow.com/a/25387570
    def exists(self, table_name, **search_params):
        """Ensure object exists in DB.

        :param table_name: A string. Name of the table were the object is to be located.
        :param search_params: kwargs where keys are column names. Values must be exact match,
            joined with AND in the SQL query.
        """
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
