# Helper functions for SG Bus Timings Web Application

import requests
import MySQLdb
from flask import render_template, session, redirect
from configparser import ConfigParser
import datetime
from functools import wraps
""" mySQL password in pythonanywhere: password250691 """


def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
 

def read_db_config(filename='config.ini', section='mysql'):
    """ Read database configuration file and return a dictionary object
    :param filename: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    """
# create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)
 
# get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))
 
    return db


# Query USERVIEWS table, filtering for ID
def query_view(ID, uniqueFlag=False, view=False):
    try:
        conn = MySQLdb.connect(**read_db_config())
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        if not uniqueFlag:
            if view:
                query = "SELECT * FROM USERVIEWS WHERE ID = %s AND VIEW = %s"
            else:
                query = "SELECT * FROM USERVIEWS WHERE ID = %s"
        else:
            query = "SELECT * FROM UNIQUEVIEW WHERE ID = %s"
        
        if view:
            cursor.execute(query, (ID, view)) 
        else:
            cursor.execute(query, (ID,))            
        rows = cursor.fetchall()        
        print("Total Rows: ", cursor.rowcount)
        res = rows    
    except:
        print("Error") 
        res = None
    finally:
        cursor.close()
        conn.close()
        return res


# Helper function to query all rows from USERVIEWS table
def query_all():
    try:
        conn = MySQLdb.connect(**read_db_config())
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERVIEWS")
        rows = cursor.fetchall()        
        print("Total Rows: ", cursor.rowcount)
        return rows    
    except:
        print("Error")        
    finally:
        cursor.close()
        conn.close()
        

# Validate if USERNAME is valid
def validate_user(username):
    """Return true if username available, else false, in JSON format"""
    try:
        conn = MySQLdb.connect(**read_db_config())
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USER WHERE USERNAME = %s", (username,))
        rows = cursor.fetchall()        
        res = False if len(rows) == 1 else True
    except:
        print("Error")
        res = False
    finally:
        cursor.close()
        conn.close()
        return res
        
# Insert into USER TABLE when a user registers for an account
def insert_user(username, pwd):
    
    # Validation for valid usernames
    if not validate_user(username):
        return         
    
    # Insertion SQL
    query = "INSERT INTO USER(USERNAME,HASH) VALUES(%s,%s)"
    args = (username, pwd)
    
    try:
        conn = MySQLdb.connect(**read_db_config())
        cursor = conn.cursor()
        cursor.execute(query, args)                   
        conn.commit()    
    except:
        print("Error")    
    finally:
        cursor.close()
        conn.close()
        return 1
    
    
# Select max ID from USER table to store into session
def selectMaxUser():
    try:
        conn = MySQLdb.connect(**read_db_config())
        cursor = conn.cursor()
        cursor.execute("select max(ID) from user")     
        ID = cursor.fetchall()[0][0]
    except:
        print("Error")
        ID = None
    finally:
        cursor.close()
        conn.close()
        return ID
    

# Create View in UNIQUEVIEW
def create_view(ID, view):
    query = "INSERT INTO UNIQUEVIEW(VIEW,ID,IDVIEW) VALUES(%s,%s,%s)"
    args = (view, ID, str(ID) + view)
    
    try:
        conn = MySQLdb.connect(**read_db_config())
        cursor = conn.cursor()
        cursor.execute(query, args)     
        conn.commit()
        print("Created a new view")
        res = 1
    except:
        print("Error")
        res = None        
    finally:
        cursor.close()
        conn.close()
        return res

# Insert into USERVIEWS TABLE the View for a user
# Param: ID: 1
# Param: view: "home"     
# Param: viewbusstopservice: "50189|145"
def insert_view(ID, view, viewbusstopservice):
    query = "INSERT INTO USERVIEWS(ID,VIEW,VIEWBUSSTOPSERVICE) VALUES(%s,%s,%s)"
    args = (ID, view, viewbusstopservice)
    
    # Validation to check service exist in bus stop number
    bs = int(viewbusstopservice.split('|')[0])
    service = viewbusstopservice.split('|')[1]
    data = queryAPI('ltaodataservice/BusArrivalv2?',
                    { 'BusStopCode': bs }
                   )
    if not service in [x['ServiceNo'] for x in data['Services']]:
        print('Service does not exist in Bus Stop')
        return 2
    
    try:
        conn = MySQLdb.connect(**read_db_config())
        cursor = conn.cursor()
        cursor.execute(query, args)                 
        conn.commit()    
        print("Inserted a new view")
        res = 1
    except:
        print("Error")
        res = None      
    finally:
        cursor.close()
        conn.close()
        return res
        
# Delete a particular view from USERVIEWS and UNIQUEVIEW table
def delete_view(ID, view, viewID=False):
    query = "DELETE FROM USERVIEWS WHERE ID = %s AND VIEW = %s"
    query2 = "DELETE FROM UNIQUEVIEW WHERE ID = %s AND VIEW = %s"
    query3 = "DELETE FROM USERVIEWS WHERE ID = %s AND VIEW = %s and VIEWID = %s"
    
    try:
        conn = MySQLdb.connect(**read_db_config())        
        cursor = conn.cursor()
        if viewID:
            args = (ID, view, viewID)
            cursor.execute(query3, args)
        else:
            args = (ID, view)
            cursor.execute(query, args)
            cursor.execute(query2, args)
        conn.commit()        
        print("Successful Deletion")
        res = 1
    except:
        print("Error")
        res = None
    finally:
        cursor.close()
        conn.close()
        return res
        
        
# Remove data from any table in the database - Use with caution 
def reset_table(tab):
    query = "TRUNCATE TABLE %s"
    args = (tab, )
    
    try:
        conn = MySQLdb.connect(**read_db_config())
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()        
        print("Successful Deletion")
    except:
        print("Error")
    finally:
        cursor.close()
        conn.close()        


# Authentication params
headers = { 'AccountKey' : 'ifYZ8D/5SOy9X87JSPq1YQ==',
            'accept' : 'application/json'}


# API call 
def queryAPI(path, params):
    headers = eval(read_db_config(section='LTAAPI')['headers'])
    uri = read_db_config(section='LTAAPI')['uri']
    return requests.get(uri + path, headers=headers, params=params).json()


# Get the bus arrival timings based on User ID and requested view
def parse_view(ID, view):  
    res = query_view(ID)
    res_filtered = [x["VIEWBUSSTOPSERVICE"] for x in res if x["VIEW"] == view]
    res_api = [queryAPI('ltaodataservice/BusArrivalv2?', \
                        { 'BusStopCode' : x.split("|")[0], \
                         'ServiceNo' : x.split("|")[1]}) for x in res_filtered]
    
    def fmtTime(ts):
      if len(ts) != 25:
          return "NA"
      
      diff = str(datetime.datetime.strptime(ts[:19],"%Y-%m-%dT%H:%M:%S") - \
                 (datetime.datetime.utcnow() + datetime.timedelta(hours=+8)))[:7]
      if diff == "-1 day,":
          return "Arrived"
      else:
          return diff
    
    def getBusTimings(data):
        if data['Services'] == []:
            return ["Service has ended"]
        else:
            return [fmtTime(data['Services'][0]['NextBus'+ ('' if x == 0 else \
                     str(x + 1))]['EstimatedArrival']) for x in range(3)]
    
    return dict(zip(res_filtered,[getBusTimings(x) for x in res_api]))


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
