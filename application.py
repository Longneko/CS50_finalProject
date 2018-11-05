import os
import json

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.routing import Map, Rule

from backend.Recipe import Recipe, Content
from backend.Ingredient import Ingredient
from backend.User import User
from backend.DBHandler import DBHandler
from backend.DBEntry import FoodEncoder, Allergy, IngredientCategory
from helpers import apology, login_required, is_string, is_iterable, is_content

# Configure application
app = Flask(__name__)

# Enable some  type testing and zip() in Jinja tempaltes
app.jinja_env.filters['zip'] = zip
app.jinja_env.filters['is_string'] = is_string
app.jinja_env.filters['is_iterable'] = is_iterable
app.jinja_env.filters['is_content'] = is_content

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure db access and JSON encoder
db = DBHandler()
enc = FoodEncoder(indent = 2)


@app.route("/")
@login_required
def index():
    # <TODO>
    """Show user's home page"""

    kwargs = {
        "rows": {}
    }

    return render_template("index.html", **kwargs)


@app.route("/admin")
@login_required
def admin():
    """Show admin main page"""

    return render_template("admin.html", rows=False)


@app.route("/admin/allergies", methods=["GET", "POST"])
@login_required
def admin_allergies():
    """Show allergies admin page for GET.
    Write new allergies to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        rows = db.get_summary("allergies", name_sort=True)
        return render_template("allergies.html", rows=rows)

    # User reached route via POST (as by submitting a form via POST)
    name = request.form.get("name")
    try:
        db_id = int(request.form.get("db_id"))
        if not db_id:
            db_id = None
    except:
        db_id = None

    allergy = Allergy(name, db_id)

    try:
        result = db.write(allergy, overwrite=True)
    except:
        result = False

    if result:
        flash("Changes saved successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("admin/allergies")


@app.route("/admin/ingredient_categories", methods=["GET", "POST"])
@login_required
def admin_ingredient_categories():
    """Show ingredient category admin page for GET.
    Write new ingredient category to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        rows = db.get_summary("ingredient_categories", name_sort=True)
        return render_template("ingredient_categories.html", rows=rows)

    # User reached route via POST (as by submitting a form via POST)
    name = request.form.get("name")
    try:
        db_id = int(request.form.get("db_id"))
        if not db_id:
            db_id = None
    except:
        db_id = None

    ing_category = IngredientCategory(name, db_id)
    try:
        result = db.write(ing_category, overwrite=True)
    except:
        result = False

    if result:
        flash("Changes saved successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("admin/ingredient_categories")


@app.route("/admin/ingredients", methods=["GET", "POST"])
@login_required
def admin_ingredients():
    """Show ingredients admin page for GET.
    Write new ingredients to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        rows = db.get_summary("ingredients", name_sort=True)
        categories = db.get_rows("ingredient_categories", "name ASC")
        allergies = db.get_rows("allergies", "name ASC")

        return render_template("ingredients.html", rows=rows, categories=categories, allergies=allergies)

    # User reached route via POST (as by submitting a form via POST)
    name = request.form.get("name")
    try:
        db_id = int(request.form.get("db_id"))
        if not db_id:
            db_id = None
    except:
        db_id = None

    category_id = request.form.get("category_id")
    category = db.fetch_ingredient_category(category_id)
    allergy_ids = request.form.getlist("allergies")
    allergies = set()
    for a_id in allergy_ids:
        allergies.add(db.fetch_allergy(a_id))

    ingredient = Ingredient(name, category, db_id, allergies)
    try:
        result = db.write(ingredient, overwrite=True)
    except:
        result = False

    if result:
        flash("Changes saved successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("admin/ingredients")


@app.route("/admin/recipes", methods=["GET", "POST"])
@login_required
def admin_recipes():
    """Show recipes admin page for GET.
    Write new recipes to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        # get recipe list for the table
        rows = db.get_summary("recipes", name_sort=True)
        ingredients = db.get_rows("ingredients")

        # contruct a list of tuple of contents of each recipe for the table
        contents = db.get_rows("recipe_contents")
        recipe_contents = {}
        for c in contents:
            recipe_id = c["recipe_id"]
            ingredient_id = c["ingredient_id"]
            ingredient_name = db.fetch_ingredient(ingredient_id).name

            amount = c["amount"]
            if not amount:
                amount = ""

            units = c["units"]
            if not units:
                units = ""
            content = (ingredient_name, amount, units)
            try:
                recipe_contents[recipe_id].append(content)
            except:
                recipe_contents[recipe_id] = [content]

        return render_template("recipes.html", rows=rows, ingredients=ingredients, recipe_contents=recipe_contents)

    # User reached route via POST (as by submitting a form via POST)
    name = request.form.get("name")
    try:
        db_id = int(request.form.get("db_id"))
        if not db_id:
            db_id = None
    except:
        db_id = None

    instructions = request.form.get("instructions")

    contents = set()
    try:
        form_contents = json.loads(request.form.get("contents"))
    except:
        form_contents = None

    for fc in form_contents:
        ingredient = db.fetch_ingredient(fc["ingredient_id"])

        try:
            amount = float(fc["amount"])
        except:
            amount = 0

        units = fc["units"]
        if fc["units"] == "":
            units = None

        contents.add(Content(ingredient, amount, units))

    recipe = Recipe(name, db_id, contents, instructions)
    try:
        result = db.write(recipe)
    except:
        result = False

    if result:
        flash("Changes saved successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("admin/recipes")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        name = request.form.get("username")
        if not name:
            return apology("must provide username", 403)

        # Ensure password was submitted
        password = request.form.get("password")
        if not password:
            return apology("must provide password", 403)

        # Ensure user exists and querry for credentials
        user = db.fetch_user(name=name)
        if not user:
            return apology("user does not exist", 403)

        # Ensure password is correct
        if not check_password_hash(user.password_hash, password):
            return apology("invalid username or password", 403)

        # Remember which user has logged in
        session["user_id"] = user.db_id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        name = request.form.get("username")
        if not name:
            return apology("must provide username")

        # Querry database and check if the username is already taken
        if db.exists("users", name=name):
            return apology("this username is already taken")

        # Ensure both passwords were submitted
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or not confirmation:
            return apology("must provide password and its confirmation")

        # Ensure passwords match
        if not password == confirmation:
            return apology("passwords do not match")

        # Store a user entry in the database
        pass_hash = generate_password_hash(password)
        user = User(name, pass_hash)
        user.db_id = db.write(user)

        if not user.db_id:
            return apology("something went wrong :'(")

        # Log the user in
        return login()

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Forget any user_id
        session.clear()

        return render_template("register.html")

@app.route("/json", methods=["GET", "POST"])
@login_required
def get_JSON():
    """Get JSON repr of an oject"""
    if request.method == "POST" and request.form:
        obj_type = request.form.get("obj_type")
        db_id = request.form.get("db_id")
    if request.method  == "GET"and request.args:
        obj_type = request.args.get("obj_type")
        db_id = request.args.get("db_id")
    try:
        db_id = int(db_id)
    except:
        pass

    d = {
        "allergy":             lambda x: db.fetch_allergy(x),
        "ingredient_category": lambda x: db.fetch_ingredient_category(x),
        "ingredient":          lambda x: db.fetch_ingredient(x),
        "recipe":              lambda x: db.fetch_recipe(x),
    }
    obj = d[obj_type](db_id)

    response = app.response_class(
        response=enc.encode(obj),
        mimetype='application/json'
    )

    return response

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
