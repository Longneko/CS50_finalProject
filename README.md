Work in progress (name is TBD)

This is an entry for the Harward's CS50 (on edX). It is a web-app that allows users to get a meal suggestions based on their preferences. Suggestions include recipes for said meals. Basically, this is a simplified set of ideas completely ripped off of numerous such apps on the marked, namely Mealime (Thank you guys for being you!) :D.

Aside from the end-user intended experience, this app also provides (or rather will eventually) an admin UI that allows to manage the DB via a web browser e.g. create meals and their constituents.

# Available features:
* DB interface (sqlite3):
  - Initializing new DB with set schema
  - Editing exisiting DB (adding new objects and editing existing ones)
  - Fetching select objects
  - Fetching summary tables (used in Admin interface)
* Web application (Flask):
  - Returning JSON-encoded objects in reponse to a POST request
  - Admin UI: managing meal constituents (allergies, ingredients and their categories, recipes)
  - End-user UI: registration, login, account settings editing (allergies only atm)

# Roadmap
(not necessarily in that order):
* DB interface:
  - Deleting objects (and resolving dependencies)
  - generating meal plans based on user preferences (allergies)
  - storing users' active meal plans
* Web application:
  - Admin UI: managing user admin access
  - End-user UI: displaying and managing user's meal plans
