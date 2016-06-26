import os
import sqlite3
from flask import Flask, request, render_template, url_for, g, redirect, flash
import pyowm, json


# replace with API key
API_key = 'b631d429365b4f37eaad3a853e2d2234'
# create global OWM object
owm = pyowm.OWM(API_key)


# create app
app = Flask(__name__)

# app configuration
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flask-weather-app.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASK-WEATHER-APP_SETTINGS', silent=True)


def connect_db():
    """ Connect to database """
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    '''
    Opens a new database connection if there is none yet for the
    current application context
    '''
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    '''
    Closes the database again at the end of request
    '''
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    '''
    Initialize and load city information to database
    '''
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    with open('city.list.json') as fp:
        for line in fp:
            j = json.loads(line)
            db.cursor().execute('insert into cities (id, city, country_code, lon, lat) values (?, ?, ?, ?, ?)',
                               (j['_id'], j['name'], j['country'], j['coord']['lon'], j['coord']['lat']))
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    ''' Initializes the database '''
    init_db()
    print 'Initialized the database.'


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def show_weather():
    try:
        assert request.form['city'] != '' and request.form['country_code'] != ''
    except AssertionError:
        return render_template('index.html', error='All fields must be filled')
    else:
        city = request.form['city'].encode('utf-8')
        country_code = request.form['country_code'].encode('utf-8')
        try:
            id = search_db(city, country_code)
        except IndexError:
            return render_template('index.html', error='Invalid input')
        else:
            obs = owm.weather_at_id(id)
            loc = obs.get_location()
            city = loc.get_name()
            weather = obs.get_weather()
            temp= weather.get_temperature(unit='celsius')
            status = weather.get_status()
            detail = weather.get_detailed_status()
            return render_template('form-action.html',  city=city, country_code=country_code.upper(), temp=temp, status=status, detail=detail)

def search_db(city, code):
    db = get_db()
    q = db.cursor().execute("select id from cities where country_code=? and city like ? limit 1", (code, city.decode('utf-8').capitalize()))
    result = [y for x in q for y in x]
    return int(result[0])
