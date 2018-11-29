import os
import urllib.request
import locale
import re

from functools import wraps
from flask import redirect, render_template, request, session
from jinja2 import evalcontextfilter, Markup, escape

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


# Filter for Jinja
def categories(recipe):
    """Return sorted list of unique categories among recipe ingredients"""
    categories = {c.ingredient.category.name for c in recipe.contents}
    categories_sorted = [c for c in categories]
    categories_sorted.sort()

    return categories_sorted


# Filter for Jinja. Returns a string where newline chars are  replaced with <br> tags and <p> wraps
# http://jinja.pocoo.org/docs/2.10/api/#custom-filters
_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result
