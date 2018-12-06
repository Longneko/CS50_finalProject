from backend.DBEntry import DBEntry, to_db_obj_name

class IngredientCategory(DBEntry):
    """Categorizes ingredients"""
    table_main = "ingredient_categories"
    associations = [
        ("ingredients","category_id", False)
    ]

    @classmethod
    def get_summary(cls, db, name_sort=False):
        """Return summary table for all IngredientCategory objects in DB as dictionary list.
        Table contains columns:
        id: category db_id.
        name: category name.
        dependents: number of other class entries referencing this id as a foreign key.

        param name_sort: A boolean. If True, summary will be recursively sorted by
            object name ascending.
        """
        table_main = to_db_obj_name(cls.table_main)
        db.c.execute(
            'SELECT ingredient_categories.id, ingredient_categories.name, '
            '  COUNT(ingredients.id) as dependents '
            'FROM ingredient_categories '
            'LEFT JOIN ingredients ON ingredient_categories.id = ingredients.category_id '
            'GROUP BY ingredient_categories.id '
            'ORDER BY ingredient_categories.id ASC'
        )
        rows = db.c.fetchall()
        summary = [{x: y for x, y in zip(row.keys(), row)} for row in rows]

        if name_sort:
            summary.sort(key=lambda x: x["name"].lower())

        return summary
