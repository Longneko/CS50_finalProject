import os
import json
from sqlite3 import Error as Sqlite_error

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.routing import Map, Rule

from backend.Allergy import Allergy
from backend.IngredientCategory import IngredientCategory
from backend.Ingredient import Ingredient
from backend.Recipe import Recipe, Content
from backend.User import User
from backend.DBHandler import DBHandler
from backend.DBEntry import FoodEncoder
from helpers import apology, login_required, is_content

# Configure application
app = Flask(__name__)

# Enable some  type testing and zip() in Jinja tempaltes
app.jinja_env.filters['zip'] = zip
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


# TESTING ONLY. TO BE REMOVED!!!
@app.route("/test_json")
@login_required
def test_json():
    """Test fetching objects in JSON"""

    return render_template("test_json.html")


@app.route("/admin")
@login_required
def admin():
    """Show admin main page"""
    return render_template("admin.html")


@app.route("/admin/allergies", methods=["GET", "POST"])
@login_required
def admin_allergies():
    """Show allergies admin page for GET.
    Write new allergies to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        rows = Allergy.get_summary(db, name_sort=True)
        return render_template("allergies.html", rows=rows)

    # User reached route via POST (as by submitting a form via POST)
    # Fetch attributes for the allergy category from the form
    name = request.form.get("name")
    try:
        id = int(request.form.get("id"))
        if not id:
            id = None
    except ValueError:
        id = None

    # Construct the new IngredientCategory object and commit changes to DB
    allergy = Allergy(name, db, id)
    try:
        result = allergy.write_to_db()
    except Sqlite_error as e:
        flash(str(e))
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
        rows = IngredientCategory.get_summary(db, name_sort=True)
        return render_template("ingredient_categories.html", rows=rows)

    # User reached route via POST (as by submitting a form via POST)
    # Fetch attributes for the ingredient category from the form
    name = request.form.get("name")
    try:
        id = int(request.form.get("id"))
        if not id:
            id = None
    except:
        id = None

    # Construct the new IngredientCategory object and commit changes to DB
    ing_category = IngredientCategory(name, db, id)
    try:
        result = ing_category.write_to_db()
    except Sqlite_error as e:
        flash(str(e))
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
        rows = Ingredient.get_summary(db, name_sort=True)
        categories = db.get_rows("ingredient_categories", order_by="name ASC")
        allergies = db.get_rows("allergies", order_by="name ASC")

        return render_template("ingredients.html", rows=rows, categories=categories, allergies=allergies)

    # User reached route via POST (as by submitting a form via POST)
    # Fetch attributes for the ingredient from the form
    name = request.form.get("name")
    try:
        id = int(request.form.get("id"))
        if not id:
            id = None
    except:
        id = None

    category_id = request.form.get("category_id")
    category = IngredientCategory.from_db(db=db, id=category_id)
    allergy_ids = request.form.getlist("allergies")
    allergies = {Allergy.from_db(db=db, id=id) for id in allergy_ids}

    # Construct the new Ingredient object and commit changes to DB
    ingredient = Ingredient(name, category, allergies, db, id)
    try:
        result = ingredient.write_to_db()
    except Sqlite_error as e:
        flash(str(e))
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
        rows = Recipe.get_summary(db, name_sort=True)
        ingredients = db.get_rows("ingredients")

        return render_template("recipes.html", rows=rows, ingredients=ingredients)

    # User reached route via POST (as by submitting a form via POST)
    # Fetch attributes for the recipe from the form
    name = request.form.get("name")
    try:
        id = int(request.form.get("id"))
        if not id:
            id = None
    except:
        id = None

    instructions = request.form.get("instructions")

    contents = set()
    try:
        form_contents = json.loads(request.form.get("contents"))
    except:
        form_contents = None

    for fc in form_contents:
        ingredient = Ingredient.from_db(db=db, id=fc["ingredient_id"])

        try:
            amount = float(fc["amount"])
        except:
            amount = 0

        units = fc["units"]
        if fc["units"] == "":
            units = None

        contents.add(Content(ingredient, amount, units))

    # Construct the new Recipe object and commit changes to DB
    recipe = Recipe(name, instructions, contents, db, id)
    try:
        result = recipe.write_to_db()
    except Sqlite_error as e:
        flash(str(e))
        result = False

    if result:
        flash("Changes saved successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("admin/recipes")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Show account settings for GET.
    Write new user settings to  DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        allergies = db.get_rows("allergies", order_by="name ASC")
        rows = db.get_rows("user_allergies", user_id=session.get("user_id"))
        user_allergies = {x["allergy_id"] for x in rows}

        return render_template("account.html", allergies=allergies, user_allergies=user_allergies)

    # User reached route via POST (as by submitting a form via POST)
    # Fetch User object from DB and replace its allergies set
    user = User.from_db(db=db, id=session.get("user_id"))
    allergy_ids = request.form.getlist("allergies")
    allergies = {Allergy.from_db(db, id) for id in allergy_ids}
    user.allergies = allergies

    # Commit the user changes to DB
    try:
        result = user.write_to_db()
    except Sqlite_error as e:
        flash(str(e))
        result = False

    if result:
        flash("Changes saved successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("/account")



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
        user = User.from_db(db=db, name=name)
        if not user:
            return apology("user does not exist", 403)

        # Ensure password is correct
        if not check_password_hash(user.password_hash, password):
            return apology("invalid username or password", 403)

        # Remember which user has logged in
        session["user_id"] = user.id

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
        if User.exists_in_db(db=db, name=name):
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
        password_hash = generate_password_hash(password)
        user = User(name=name, password_hash=password_hash, db=db)

        # Commit the user changes to DB
        try:
            result = user.write_to_db()
        except Sqlite_error as e:
            flash(str(e))
            result = False

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
        id = request.form.get("id")
    if request.method  == "GET"and request.args:
        obj_type = request.args.get("obj_type").lower()
        id = request.args.get("id")
    try:
        id = int(id)
    except:
        pass

    d = {
        "allergy":             lambda id: Allergy.from_db(db, id),
        "ingredient_category": lambda id: IngredientCategory.from_db(db, id),
        "ingredient":          lambda id: Ingredient.from_db(db, id),
        "recipe":              lambda id: Recipe.from_db(db, id),
        "user":                lambda id: User.from_db(db, id),
    }
    obj = d[obj_type](id)

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
