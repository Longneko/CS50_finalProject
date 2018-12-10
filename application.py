import os
import json
from sqlite3 import Error as Sqlite_error

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from backend.Allergy import Allergy
from backend.IngredientCategory import IngredientCategory
from backend.Ingredient import Ingredient
from backend.Recipe import Recipe, Content
from backend.User import User
from backend.DBHandler import DBHandler, DBError
from backend.DBEntry import FoodEncoder
from helpers import apology, login_required, admin_required, is_content, categories, nl2br, username_valid

# Configure application
app = Flask(__name__)

# Configure Jinja filters and whitespace handling
app.jinja_env.filters["zip"] = zip
app.jinja_env.filters["nl2br"] = nl2br
app.jinja_env.filters["is_content"] = is_content
app.jinja_env.filters["categories"] = categories
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Image upload settings
ALLOWED_IMG_EXTENSIONS = set(["jpg", "jpeg"])
app.config["RECIPE_IMG_PATH"] = os.path.join(app.root_path, "static/images/recipes")
app.config['MAX_CONTENT_LENGTH'] = 0.5 * 1024 * 1024 # limit max file size to 0.5MB


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
    """Show user's home page"""

    user = User.from_db(db=db, id=session.get("user_id"))
    try:
        recipe_ids = {m.id for m in user.meals}
        recipes = [Recipe.from_db(db=db, id=id) for id in recipe_ids]
    except AttributeError:
        recipes=[]

    return render_template("index.html", meals=recipes)


@app.route("/admin", defaults={"obj_type":None}, methods=["GET"])
@app.route("/admin/<string:obj_type>", methods=["GET"])
@login_required
@admin_required
def admin_display(obj_type):
    """Show admin page for selected object type"""
    template = obj_type + ".html" if obj_type else "admin.html"
    if obj_type == "allergies":
        kwargs = {"rows":Allergy.get_summary(db)}
    elif obj_type == "ingredient_categories":
        kwargs = {"rows":IngredientCategory.get_summary(db)}
    elif obj_type == "ingredients":
        kwargs = {"rows"      : Ingredient.get_summary(db),
                  "categories": db.get_rows("ingredient_categories"),
                  "allergies" : db.get_rows("allergies")}
    elif obj_type == "recipes":
        kwargs = {"rows"       : Recipe.get_summary(db),
                  "ingredients": db.get_rows("ingredients")}
    elif obj_type == "users":
        kwargs = {"rows"      : User.get_summary(db),
                  "allergies" : db.get_rows("allergies")}
    else:
        kwargs = {}

    return render_template(template, **kwargs)


@app.route("/admin/<string:obj_type>", methods=["POST"])
@login_required
@admin_required
def admin_write(obj_type):
    """Write new object to DB or edit an existing one based on submitted form"""
    # Set basic values present for all object types
    name = request.form.get("name")
    try:
        id = int(request.form.get("id"))
        if not id:
            id = None
    except ValueError:
        id = None

    # Construct object to be written
    if obj_type == "allergies":
        obj = Allergy(name, db, id)
    elif obj_type == "ingredient_categories":
        obj = IngredientCategory(name, db, id)
    elif obj_type == "ingredients":
        category_id = request.form.get("category_id")
        category = IngredientCategory.from_db(db=db, id=category_id)
        allergy_ids = request.form.getlist("allergies")
        allergies = {Allergy.from_db(db=db, id=id) for id in allergy_ids}

        obj = Ingredient(name, category, allergies, db, id)
    elif obj_type == "recipes":
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
            except KeyError:
                amount = 0
            units = fc["units"] if fc["units"] != "" else None

            contents.add(Content(ingredient, amount, units))

        obj = Recipe(name, instructions, contents, db, id)

        # Define function to be called only if object is written to DB successfully
        def if_written():
            # Apply image changes to the filesystem
            filename = str(obj.id) + ".jpg"
            if request.form.get("image-delete"):
                # Current image is to be deleted if exists
                try:
                    os.remove(os.path.join(app.config["RECIPE_IMG_PATH"], filename))
                except FileNotFoundError:
                    pass
            else:
                # New image is to be saved
                image = request.files.get("image")
                if image:
                    extension = image.filename.split(".").pop()
                    if extension in ALLOWED_IMG_EXTENSIONS:
                        image.save(os.path.join(app.config["RECIPE_IMG_PATH"], filename))
                    else:
                        flash("Only .jpg, .jpeg images allowed", category=danger)
    elif obj_type == "users":
        obj = User.from_db(db, id)
        obj.is_admin = request.form.get("is_admin")
        obj.name = request.form.get("name")
    else:
        return ("Object type not found")


    try:
        result = obj.write_to_db()
    except:
        result = False

    if result:
        flash("Changes saved successfully!")
        try:
            if_written()
        except UnboundLocalError:
            pass
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("admin/" + obj_type)


@app.route("/admin/remove/<string:obj_type>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_remove(obj_type):
    """Remove an object from DB"""
    if request.method == "POST" and request.form:
        id = request.form.get("id")
    if request.method  == "GET" and request.args:
        id = request.args.get("id")
    try:
        id = int(id)
    except:
        id = None

    if not id:
        return("Missing or invalid params")

    d = {
        "allergies"            : lambda db, id: Allergy.from_db(db, id).remove_from_db(),
        "ingredient_categories": lambda db, id: IngredientCategory.from_db(db, id).remove_from_db(),
        "ingredients"          : lambda db, id: Ingredient.from_db(db, id).remove_from_db(),
        "recipes"              : lambda db, id: Recipe.from_db(db, id).remove_from_db(),
        "users"                : lambda db, id: User.from_db(db, id).remove_from_db(),
    }
    try:
        d[obj_type](db, id)
        # If a recipe was removed remove its image
        if obj_type == "recipes":
            filename = str(id) + ".jpg"
            try:
                os.remove(os.path.join(app.config["RECIPE_IMG_PATH"], filename))
            except FileNotFoundError:
                pass
        flash("Entry deleted successfully!")
    except KeyError:
        return ("Object type not found")
    except DBError:
        flash("Cannot delete entry with dependents (referenced by other entries)!", category="danger")
    except:
        flash("Something went wrong :(", category="danger")

    return redirect("admin/" + obj_type)


@app.route("/account/<string:form>", methods=["POST"])
@app.route("/account", defaults={"form":None}, methods=["GET"])
@login_required
def account(form):
    """Show account settings for GET.
    Write new user settings to  DB for POST.
    """
    user = User.from_db(db=db, id=session.get("user_id"))

    # User reached "/account" route via GET (as by clicking a link or via redirect)
    if request.method == "GET" and not form:
        allergies = db.get_rows("allergies", order_by="name ASC")
        user_allergies = {x.id for x in user.allergies}

        return render_template("account.html", allergies=allergies, user_allergies=user_allergies)

    # User reached "/account/<form>" route via POST (as by submitting a form via POST)
    if form == "allergies":
        allergy_ids = request.form.getlist("allergies")
        allergies = {Allergy.from_db(db, id) for id in allergy_ids}
        user.allergies = allergies
    elif form == "password":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        if not current_password:
            flash("Must provide valid current password", category="danger")
            return redirect("account")
        if not all([new_password, confirmation]):
            flash("Must provide new password and repeat it", category="danger")
            return redirect("account")
        if not new_password == confirmation:
            flash("New passwords don't match", category="danger")
            return redirect("account")
        if not check_password_hash(user.password_hash, current_password):
            flash("Incorrect current password", category="danger")
            return redirect("account")

        user.password_hash = generate_password_hash(new_password)

    # Commit the user changes to DB
    try:
        result = user.write_to_db()
    except:
        result = False

    if result:
        flash("Changes saved successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("/account")



@app.route("/login", methods=["GET", "POST"])
def login(first=False):
    """Log user in"""

    # Forget any user_id
    session.clear()

    if first:
        flash("We recommend to visit the 'Account' page if you have any food allergies")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure valid username was submitted
        try:
            name = username_valid(request.form.get("username"))
        except TypeError:
            name = None
        if not name:
            return apology("must provide valid username", 403)

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
        session["is_admin"] = user.is_admin

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

        # Ensure valid username was submitted
        try:
            name = username_valid(request.form.get("username"))
        except TypeError:
            name = None
        if not name:
            return apology("must provide valid username")

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
        except:
            result = False

        # Log the user in
        return login(first=True)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Forget any user_id
        session.clear()

        return render_template("register.html")

@app.route("/action", methods=["GET", "POST"])
@login_required
def action():
    """Perform a command sent from user interface via form or AJAX.
    Currently includes adding/removing user's meals from meal plans"""
    if request.method == "POST" and request.form:
        command = request.form.get("command")
        id = request.form.get("id")
    if request.method  == "GET" and request.args:
        command = request.args.get("command").lower()
        id = request.args.get("id")
    try:
        id = int(id)
    except:
        id = None

    if not command or not id:
        return("Missing or invalid params")

    user = User.from_db(db=db, id=session.get("user_id"))

    d = {
        "add_meal"   : lambda user, id: user.add_meal(id),
        "remove_meal": lambda user, id: user.remove_meal(id),
    }
    try:
        obj = d[command](user, id)
    except KeyError:
        return("Missing or invalid params")

    return("success")


@app.route("/json", methods=["GET", "POST"])
@login_required
def get_JSON():
    """Get JSON repr of an object"""
    if request.method == "POST" and request.form:
        obj_type = request.form.get("obj_type")
        id = request.form.get("id")
    if request.method  == "GET" and request.args:
        obj_type = request.args.get("obj_type").lower()
        id = request.args.get("id")
    try:
        id = int(id)
    except:
        id = None

    if obj_type in ["user", "valid_meals"]:
        if not session.get("is_admin") or not id:
            id = session.get("user_id")
    elif not id:
        return("Missing or invalid params")


    # Users can access only their own user obj and valid_meals
    user_id = session.get("user_id")
    d = {
        "allergy"            : lambda db, id: Allergy.from_db(db, id),
        "ingredient_category": lambda db, id: IngredientCategory.from_db(db, id),
        "ingredient"         : lambda db, id: Ingredient.from_db(db, id),
        "recipe"             : lambda db, id: Recipe.from_db(db, id),
        "user"               : lambda db, id: User.from_db(db, id),
        "valid_meals"        : lambda db, id: User.from_db(db, id).get_valid_recipes_id(),
    }
    try:
        obj = d[obj_type](db, id)
    except KeyError:
        return("Missing or invalid params")

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
