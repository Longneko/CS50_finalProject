# FoodApp

Originally, this was my final project for the Harward's CS50 (on edX). But it got sprinkled with jsuta bit of extra functional and ReadMe gibberish. It is a web-app that allows users to get meal suggestions based on their preferences. Suggestions include recipes for said meals. Basically, this is a simplified set of ideas completely ripped off of numerous such apps on the marked, namely Mealime (Thank you guys for being you!) :D.

Aside from the end-user intended experience, this app also provides an admin UI that allows to manage the DB via a web browser e.g. create meals and their constituents.

See it does: https://youtu.be/o0ck04ZR7UI

## Available features:
* DB interface (sqlite3):
  - Initializing new DB with set schema
  - Editing exisiting DB (adding, editing, deletion)
  - Fetching select objects
  - Fetching summary tables (used in Admin interface)
  - Generating and managing meal plans based on user preferences (allergies)
* Web application (Flask):
  - Returning JSON-encoded objects in reponse to a POST request
  - Admin UI: managing meal constituents (allergies, ingredients and their categories, recipes)
  - Admin UI: managing users' admin access
  - End-user UI: registration, login, account settings editing (allergies only atm)
  - End-user UI: displaying and managing user's meal plans

## Roadmap (maybe):
(not necessarily in that order)
* Web application:
  - Admin UI: managing users' meal related data
  - CSS and layout more fit for human beings (partially there)
* General:
  - User's favorite recipes functional
  - Ingredients' amount units standartization and subsequent Shopping list
  - Ingredients' states
  - Auxuliary recipes (recipes of complex ingredients likes stocks, doughs etc. availalbe on demand in a separate menu)

## Requirements:
- Python 3.6
  - Flask 1.0
  - Jinja 2.1
  - Werkzeug 0.14.1
- HTML5
- Web UI also uses Bootstrap 4.1, Jquery 3.1.1 and Font Awesome icons imported online.

## Credits:
- Default recipe image by imaginasty (PS'ed by D. Neverov): https://www.shutterstock.com/image-vector/illustrations-food-shape-cute-cat-milkshake-1132425281

# Quick start:
## Running the App
Go to the root folder of the application and run the follownig commands:
```
$ export FLASK_APP=application.py
$ python -m flask run
```
This will start the application locally on a default http://127.0.0.1:5000/ host. Such application will be visible on your computer only. Should you want it to be publicly visible, use the following commands:
```
$ export FLASK_APP=application.py
$ flask run --host=0.0.0.0
```
Please, refer to Flask's quickstart(http://flask.pocoo.org/docs/1.0/quickstart/) or deployment(http://flask.pocoo.org/docs/1.0/deploying/#deployment) for more detials if you are taking this app seriously for some reason.

## Content
The app comes with a starter-pack database containing 10 complete recipes and a set of the most common food allergies.
It also has a single user with 'admin' as both username and password. It can be used to grant admin access via the web interface to any of the users that register.

Should you decide to flush the DB and start your own, please, remove the 'backend/food.db' file that is the app's database and run following command to initialize a new one:
```
$ python3 new_db.py
```
This will create an empty DB with the same schema. With the exception of still having the 'admin' user not to have  to grant admin priviliges to new users manually within the DB or Python code.


# NSFAQ (Not So Frequently Asked Questions)
**Q:** But Valerii, why would you use Python's Sqlite3 instead of using SQLAlchemy ORM? Wouldn't that be a more logical choice?
**A:** Of course it would. Well, I underestimated the amount of work I'd have to end up putting in when I started the project, and mastering new libraries seemed scary and painful at the time. Well, I  suffered even more pain eventually. Good, I deserved it. On the bright side, I got to show off some knowledge of SQLite in the code.

**Q:** Why would anyone even read this README all the way to this point?
**A:** Beats me.
