import sqlite3

DEFAULT_DB_PATH = "backend/food.db"

class DBHandler(object):
    """Handles storage and retrieval of within a DB"""
    def __init__(self, db_path=DEFAULT_DB_PATH):
        """ :param db_path: A string, path to the target DB"""
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
        objects = [to_db_obj_name(table_name)]
        needle = tuple()
        for key, value in search_params.items():
            objects.append(to_db_obj_name(key))
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


class DBError(Exception):
    def __init__(self, message, params=None):
        super().__init__(message)
        self.params = params


# DB object interpolation taken from Martijn Pieters's answer here:
# https://stackoverflow.com/a/25387570
def to_db_obj_name(s):
    """Returns string modified so that it can be used as DB object (e.g table, column, etc.) name
    within double quotes of a query string.
    This method DOES NOT provide properly prevent injection and should only be used for internal values.
    """
    return s.replace('"', '""')
