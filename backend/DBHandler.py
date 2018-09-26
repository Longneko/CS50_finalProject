import sqlite3

from backend.Ingredient import Ingredient
from backend.Recipe import Recipe, Content

DEFAULT_DB_PATH = 'backend/food.db'

class DBHandler(object):
    """Handles storage and retrieval of within a DB.

    :param db_path: A string, path to the target DB.
    """
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db = sqlite3.connect(db_path)
        self.c = self.db.cursor()
        self.c.execute('PRAGMA foreign_keys = ON;')
        self.db.commit()

    def __del__(self):
        self.db.close()

    def create_schema(self):
        """Creates the required schema in an empty DB"""
        self.c.executescript("""
                CREATE TABLE ingredient_categories(
                  id INTEGER PRIMARY KEY,
                  name TEXT,
                  CONSTRAINT name_unique UNIQUE (name)
                );

                CREATE TABLE ingredients(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL,
                  category_id INTEGER NOT NULL,
                  CONSTRAINT name_unique UNIQUE (name),
                  FOREIGN KEY (category_id) REFERENCES ingredient_categories(id)
                );

                CREATE TABLE allergies(
                  id INTEGER PRIMARY KEY,
                  name TEXT,
                  CONSTRAINT name_unique UNIQUE (name)
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
                  name TEXT NOT NULL,
                  instructions TEXT,
                  CONSTRAINT name_unique UNIQUE (name)
                );

                CREATE TABLE recipe_contents(
                  recipe_id INTEGER NOT NULL,
                  ingredient_id INTEGER NOT NULL,
                  units INTEGER,
                  unit_type TEXT DEFAULT NULL,
                  PRIMARY KEY (recipe_id, ingredient_id),
                  FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                  FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
                );
                """)

        self.db.commit()

    def write_ingredient_category(self, name):
        """Writes a new ingredient category to the DB"""
        cat = (name,)
        self.c.execute("INSERT INTO ingredient_categories (name) VALUES (?)", cat)
        self.db.commit()
