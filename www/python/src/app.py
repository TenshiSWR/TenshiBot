from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import abort, Flask, redirect, render_template, request, session, url_for
from json import loads
from multiprocess import Process
import mwoauth
import os
from tools.misc import get_database, queryandclose

app = Flask(__name__)
data, last_query_time = None, None
load_dotenv()
USER_AGENT = loads(os.getenv("USER-AGENT"))
app.secret_key = loads(os.getenv("WSGI-SECRET"))
_AUTH = mwoauth.ConsumerToken(loads(os.getenv("APP-OAUTH"))[0], loads(os.getenv("APP-OAUTH"))[1])
APP_TOKEN = loads(os.getenv("APP-OAUTH"))[0]


@app.route("/")
def index():
    if "request_token" in session and request.query_string and not "access_token" in session:
        access_token = mwoauth.complete("https://en.wikipedia.org/w/index.php", _AUTH, mwoauth.RequestToken(**session["request_token"]), request.query_string)
        identity = mwoauth.identify("https://en.wikipedia.org/w/index.php", _AUTH, access_token)
        session["access_token"], session["username"] = dict(zip(access_token._fields, access_token)), identity["username"]
        return redirect(url_for("wikicup"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return "You are already logged in as {}".format(session["username"])
    r, token = mwoauth.initiate("https://en.wikipedia.org/w/index.php", _AUTH)
    session["request_token"] = dict(zip(token._fields, token))
    return redirect(r)


@app.route("/tasks")
def tasks():
    global data, last_query_time
    if (not data or not last_query_time) or (datetime.utcnow().replace(tzinfo=None)-timedelta(seconds=5)) > last_query_time.replace(tzinfo=None):
        db, cursor = get_database()
        cursor.execute("SELECT * FROM task_status ORDER BY task ASC;")
        data = cursor.fetchall()
        last_query_time = datetime.utcnow()
        db.close()
    if any([True for x in data if x[4] != "N/A"]):
        empty = False
    else:
        empty = True
    activity = {}
    time_elapsed = {}
    for item in data:
        start, end = item[2], item[3]
        if start and end:
            if start > end:
                activity[item[0]] = start
            else:
                activity[item[0]] = end
        elif start and not end:
            activity[item[0]] = start
        elif not start and end:
            activity[item[0]] = end
        else:
            activity[item[0]] = "?"
        if activity[item[0]] != "?":
            time_elapsed[item[0]] = datetime.utcnow().replace(tzinfo=None)-activity[item[0]]
            if time_elapsed[item[0]].days > 31:
                data[data.index(item)][5] = "N/A"  # Likewise with below, these should be removed after a while
                queryandclose("UPDATE task_status SET status = 'N/A' WHERE task = %(task)s AND site_name = %(site_name)s;", {"task": item[0], "site_name": item[4]})
            elif time_elapsed[item[0]].days < 1 and (time_elapsed[item[0]].seconds // 60) >= 60:
                time_elapsed[item[0]] = "{} hours, {} minutes".format(time_elapsed[item[0]].seconds // 3600, (time_elapsed[item[0]].seconds % 3600) // 60)
            elif time_elapsed[item[0]].days < 1 and (time_elapsed[item[0]].seconds // 60) < 60:
                time_elapsed[item[0]] = "{} minutes, {} seconds".format(time_elapsed[item[0]].seconds // 60, time_elapsed[item[0]].seconds % 60)
            else:
                time_elapsed[item[0]] = None  # I'd prefer not to see unlisted copyright problems hasn't been run for 20,160 minutes
        else:
            time_elapsed[item[0]] = "?"
    return render_template("tasks.html", activity=activity, data=data, empty=empty, time_elapsed=time_elapsed)


@app.route("/wikicup", methods=["GET", "POST"])
def wikicup():
    global wikicup_round
    if not "username" in session:
        return redirect(url_for("login"))
    elif not session["username"] in ["Cwmhiraeth", "Epicgenius", "Frostly", "Guerillero", "Lee Vilenski", "Tenshi Hinanawi"]:
        abort(403)
    if request.method == "GET":
        return render_template("wikicup.html", started=False, wikicup_round=wikicup_round)
    else:
        wikicup_round = request.form.get("round")
        queryandclose("UPDATE misc SET wikicup_round = %(wikicup_round)s, wikicup_judge_username = %(wikicup_judge_username)s;", {"wikicup_round": wikicup_round, "wikicup_judge_username": session["username"]})
        Process(target=lambda: __import__("tasks/wikicup_submissions")).start()
        return render_template("wikicup.html", started=True, wikicup_round=wikicup_round)


os.chdir("../../../reports")
files = ["reports."+x[:-3] for x in os.listdir() if ".py" in x]
os.chdir("../tasks")
files = sorted(files+["tasks."+x[:-3] for x in os.listdir() if ".py" in x])
os.chdir("../www/python/src")
db, _ = get_database()
cursor = db.cursor(buffered=True)
for file in files:
    cursor.execute("SELECT task FROM task_status WHERE task = %(file)s;", {"file": file})
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO task_status(task, status) VALUES(%(task)s, 'N/A');", {"task": file})
        db.commit()
cursor.execute("SELECT wikicup_round FROM misc;")
wikicup_round = cursor.fetchone()[0]
db.close()

if not os.path.exists("replica.my.cnf"):
    app.run()
