import os
import urllib.request
import locale

from flask import redirect, render_template, request, session
from functools import wraps

from backend.Recipe import Content


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorate routes to require admin rights."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            return apology("Not found", 404)
        return f(*args, **kwargs)
    return decorated_function


# filter for Jinja
def is_content(x):
    content_keys = {"ingredient", "amount", "units"}
    try:
        return content_keys <= set(x.keys())
    except:
        return False


# filter for Jinja
def categories(recipe):
    """Return sorted list of unique categories among recipe ingredients"""
    categories = {c.ingredient.category.name for c in recipe.contents}
    categories_sorted = [c for c in categories]
    categories_sorted.sort()

    return categories_sorted
