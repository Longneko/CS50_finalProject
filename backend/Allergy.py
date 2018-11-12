from backend.DBEntry import DBEntry, to_db_obj_name

class Allergy(DBEntry):
    """An allergy that an ingredient may cause and users may list to avoid meals with
    such ingredients.
    """
    table_main = "allergies"

    @classmethod
    def get_summary(cls, db, name_sort=False):
        """Return summary table for all Allergy objects in DB as dictionary list.
        Table contains columns:
        id: allergy db_id.
        name: allergy name.
        dependents: number of other class entries referencing this id as a foreign key.

        param name_sort: A boolean. If True, summary will be recursively sorted by
            object name ascending.
        """
        table_main = to_db_obj_name(cls.table_main)
        # ingredient_allergies to be renamed to ingredient_allergies
        db.c.execute(
            'SELECT id, name, (COUNT(ingredient_id) + COUNT(user_id)) as dependents '
            'FROM allergies '
            'LEFT JOIN ingredient_allergies ON allergies.id = ingredient_allergies.allergy_id '
            'LEFT JOIN user_allergies ON allergies.id = user_allergies.allergy_id '
            'GROUP BY allergies.id '
            'ORDER BY allergies.id ASC'
                     )
        rows = db.c.fetchall()
        summary = [{x: y for x, y in zip(row.keys(), row)} for row in rows]

        if name_sort:
            summary.sort(key=lambda x: x["name"].lower())

        return summary
