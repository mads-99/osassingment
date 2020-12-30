from flask import Flask, render_template, redirect, url_for, request, make_response
import mysql.connector
import socket
import os
import json
import time

app = Flask(__name__)

TEXT1=os.environ.get('TEXT1', "Hackfest")
TEXT2=os.environ.get('TEXT2', "Registration")
ORGANIZER=os.environ.get('ORGANIZER', "UVCE")

time.sleep(2)
db = mysql.connector.connect(user = "root", password = "hello",
                              host = "db", database = "rsvp",
                              auth_plugin='mysql_native_password')

db_cursor = db.cursor()
table = """CREATE TABLE IF NOT EXISTS entries (
         id INT AUTO_INCREMENT PRIMARY KEY,
         name VARCHAR(30) NOT NULL,
         email VARCHAR(50) NOT NULL)"""
db_cursor.execute(table)
db_cursor.close()

class RSVP(object):
    """Simple Model class for RSVP"""
    def __init__(self, name, email, _id=None):
        self.name = name
        self.email = email
        self._id = _id

    def dict(self):
        _id = str(self._id)
        return {
            "_id": _id,
            "name": self.name,
            "email": self.email,
            "links": {
                "self": "{}api/rsvps/{}".format(request.url_root, _id)
            }
        }

    def delete(self):
        db_cursor = db.cursor()
        db_cursor.execute("DELETE FROM entries WHERE id=" + str(self._id))
        db_cursor.close()

    @staticmethod
    def find_all():
        db_cursor = db.cursor()
        db_cursor.execute("SELECT * FROM entries")
        _items = db_cursor.fetchall()
        items = []
        for item in _items:
            items.append(RSVP(item[1], item[2], item[0]))
        db_cursor.close()
        return items

    @staticmethod
    def find_one(id):
        db_cursor = db.cursor()
        db_cursor.execute("SELECT * FROM entries WHERE id=" + id)
        _items = db_cursor.fetchall()
        items = []
        for item in _items:
            items.append(RSVP(item[1], item[2], item[0]))
        db_cursor.close()
        if len(items) > 0:
            return items[0]
        else:
            return None

    @staticmethod
    def new(name, email):
        db_cursor = db.cursor()
        db_cursor.execute("INSERT INTO entries (name, email) VALUES (%s, %s)", (request.form['name'], request.form['email']))
        inserted_id = db_cursor.lastrowid
        db_cursor.close()
        return RSVP(name, email, inserted_id)

@app.route('/')
def rsvp():
    db_cursor = db.cursor()
    db_cursor.execute("SELECT * FROM entries")
    _items = db_cursor.fetchall()
    items = []
    for item in _items:
        items.append({"name": item[1], "email": item[2]})
    db_cursor.close()
    count = len(items)
    hostname = socket.gethostname()
    return render_template('profile.html', counter=count, hostname=hostname,\
                           items=items, TEXT1=TEXT1, TEXT2=TEXT2, ORGANIZER=ORGANIZER)

@app.route('/new', methods=['POST'])
def new():
    db_cursor = db.cursor()
    db_cursor.execute("INSERT INTO entries (name, email) VALUES (%s, %s)", (request.form['name'], request.form['email']))
    db_cursor.close()
    return redirect(url_for('rsvp'))

@app.route('/api/rsvps', methods=['GET', 'POST'])
def api_rsvps():
    if request.method == 'GET':
        docs = [rsvp.dict() for rsvp in RSVP.find_all()]
        return json.dumps(docs, indent=True)
    else:
        try:
            doc = json.loads(request.data)
        except ValueError:
            return '{"error": "expecting JSON payload"}', 400

        if 'name' not in doc:
            return '{"error": "name field is missing"}', 400
        if 'email' not in doc:
            return '{"error": "email field is missing"}', 400

        rsvp = RSVP.new(name=doc['name'], email=doc['email'])
        return json.dumps(rsvp.dict(), indent=True)

@app.route('/api/rsvps/<id>', methods=['GET', 'DELETE'])
def api_rsvp(id):
    rsvp = RSVP.find_one(id)
    if not rsvp:
        return json.dumps({"error": "not found"}), 404

    if request.method == 'GET':
        return json.dumps(rsvp.dict(), indent=True)
    elif request.method == 'DELETE':
        rsvp.delete()
        return json.dumps({"deleted": "true"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
