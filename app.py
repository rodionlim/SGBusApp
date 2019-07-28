# Web Application backend Controller - SG Bus Timings
"""
Author: Rodion
Date Created: 2019.07.14
Version: 0.1
 
"""
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
import MySQLdb
import json
from werkzeug.exceptions import default_exceptions, HTTPException, \
InternalServerError
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import insert_user, selectMaxUser, validate_user, apology, \
read_db_config, query_view, create_view, delete_view, insert_view, \
parse_view, login_required, extract_busStopData

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
#@app.after_request
#def after_request(response):
#    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#    response.headers["Expires"] = 0
#    response.headers["Pragma"] = "no-cache"
#    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Store bus stop details into memory
busStopDict = extract_busStopData()


@app.route("/", methods=["GET", "POST"])
def index():
    """Show Index Page"""
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
     """Log user in"""

     # Forget any user_id
     session.clear()

     # User reached route via POST (as by submitting a form via POST)
     if request.method == "POST":

         # Ensure username was submitted
         if not request.form.get("username"):
             return apology("must provide username", 400)

         # Ensure password was submitted
         elif not request.form.get("password"):
             return apology("must provide password", 400)

         # Query database for username
         try:
             conn = MySQLdb.connect(**read_db_config())
             cursor = conn.cursor()
             cursor.execute("SELECT * FROM USER WHERE USERNAME = %s", \
                            (request.form.get("username"),))
             rows = cursor.fetchall()
         except:
             print("Error")
             rows = "ERROR"
         finally:
             cursor.close()
             conn.close()
             if rows == "ERROR":
                 return apology("Unexpected error.", 400)
         
         # Ensure username exists and password is correct
         if len(rows) != 1 or not check_password_hash(rows[0][2], \
               request.form.get("password")):
             return apology("invalid username and/or password", 400)

         # Remember which user has logged in
         session["user_id"] = rows[0][0]

         # Redirect user to home page
         return redirect("/")

     # User reached route via GET (as by clicking a link or via redirect)
     else:
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

     # User reach route via POST (as by submitting a form via POST)
     if request.method == "POST":
         # Retrieve key inputs from form
         user = request.form.get("username")
         password = request.form.get("password")
         confirmation = request.form.get("confirmation")

         # Begin validation chks
         if not user:
             return apology("must provide a username", 400)
         elif not (password and confirmation):
             return apology("must provide a password", 400)
         elif password != confirmation:
             return apology("passwords do not match", 400)
         else:
             result = insert_user(user, generate_password_hash(password))
             if not result:
                 return apology("username already taken", 400)
             else:
                 # Remember which user has logged in
                 uid = selectMaxUser()
                 session["user_id"] = uid

                 # Redirect user to home page
                 return redirect("/")
     else:
         return render_template("/register.html")


@app.route("/editViews", methods=["GET", "POST"])
@login_required
def editViews():
    """Show Edit View Page"""    
    # User reach route via GET
    if request.method == "GET":
        data = query_view(session["user_id"],True)
        views = list(set([x['VIEW'] for x in data]))
        return render_template("editViews.html", views=json.dumps(views))


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    if validate_user(request.args.get("username")):
        return jsonify(True)
    else:
        return jsonify(False)
    
    
@app.route("/create", methods=["GET"])
@login_required
def createView():
    """Return true if view was created, else false, in JSON format"""
    if create_view(session["user_id"], request.args.get("viewname")):
        return jsonify(True)
    else:
        return jsonify(False)
        
        
@app.route("/deleteView", methods=["GET"])
@login_required
def deleteView():
    """Return true if view was deleted, else false, in JSON format"""
    viewID = request.args.get("viewid") if request.args.get("viewid") else False
    if delete_view(session["user_id"], request.args.get("viewname"), viewID):
        return jsonify(True)
    else:
        return jsonify(False)
        
        
@app.route("/queryView", methods=["GET"])
@login_required
def queryView():
    """Return true if view was deleted, else false, in JSON format"""
    res = query_view(session["user_id"], view=request.args.get("viewname"))
    if res:
        return jsonify(res)
    else:
        return jsonify(False)
    
    
@app.route("/insertView", methods=["GET"])
@login_required
def insertView():
    """Return true if row was inserted in view, else false, in JSON format"""
    res = insert_view(session["user_id"], view=request.args.get("viewname"), \
                      viewbusstopservice=request.args.get("bssn"))
    if res == 2:
        return jsonify("2")
    elif res == 1:
        return jsonify(True)
    else:
        return jsonify(False)
    

@app.route("/getViews", methods=["GET"])
@login_required
def getViews():
    """Generates the html for all the views a user has created"""
    allViews = query_view(session["user_id"])
    uniqueViews = query_view(session["user_id"],True)
    return render_template("/getViews.html", av=allViews, uv=uniqueViews)


@app.route("/queryAPI", methods=["GET"])
@login_required
def queryAPI():
    """Queries the LTA API to populate views"""
    view = request.args.get("viewname")
    return jsonify(parse_view(session["user_id"], view, busStopDict))


def errorhandler(e):
     """Handle error"""
     if not isinstance(e, HTTPException):
         e = InternalServerError()
     return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
     app.errorhandler(code)(errorhandler)
