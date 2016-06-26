import os
import sqlite3
from flask import Flask, request, render_template, url_for, g, redirect, flash
import pyowm, json, collections
from datetime import date, timedelta
from pyowm.exceptions.not_found_error import NotFoundError


# replace with your API key
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


def connect_db():
    '''
    Connect to database
    '''
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

def load_city_info():
    '''
    Load city info to database
    '''
    db = get_db()
    with open('city.list.json') as f:
        for line in f:
            j = json.loads(line)
            db.cursor().execute('insert into cities (id, city, country_code, lon, lat) values (?, ?, ?, ?, ?)',
                               (j['_id'], j['name'], j['country'], j['coord']['lon'], j['coord']['lat']))

def init_db():
    '''
    Initialize database
    '''
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    load_city_info()
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    '''
    Initializes the database
    '''
    init_db()
    print 'Initialized the database.'


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def show_weather():
    '''
    Gets user's input from form and creates and Observation object if data is valid,
    renders template with weather data from Observation
    '''
    # check if any field was not filled by user
    if request.form['city'] == '' or request.form['country_code'] == '':
        return render_template('index.html', error='All fields must be filled')
    else:
        city = request.form['city'].encode('utf-8')
        country_code = request.form['country_code'].encode('utf-8')
        try:
            # get city id from database
            id = search_db(city, country_code)
        except IndexError:
            return render_template('index.html', error='Invalid input')
        else:
            # retrieve weather data
            current = get_current_weather(id, country_code.upper())
            forecast = get_forecast(id)
            return render_template('form-action.html', current=current, forecast=forecast)

def search_db(city, code):
    '''
    Search database for the id of the given city and country code
    city: a string representing the city name
    code: a string representing the country code
    returns: an int if city and country code in database, raises IndexError otherwise
    '''
    db = get_db()
    q = db.cursor().execute("select id from cities where country_code=? and city like ? limit 1", (code, city.decode('utf-8').capitalize()))
    result = [y for x in q for y in x]
    return int(result[0])

def get_current_weather(id, code):
    '''
    Creates an Observation object and retrieves current weather info from it
    id: and int
    code: a string representing the country code
    returns a dict with current weather data
    '''
    data = {'country_code':code,}
    # create Observation object
    obs = owm.weather_at_id(id)
    # Observation object stores a Location object
    loc = obs.get_location()
    # get correct city name to pass to template
    data['city']= loc.get_name()
    # get weather data from Weather object stored in Observation
    weather = obs.get_weather()
    data['temp']= weather.get_temperature(unit='celsius')
    data['status'] = weather.get_status()
    data['detail'] = weather.get_detailed_status()
    return data

def get_forecast(id):
    '''
    Gets forecast for the remaining of current day and for the next 3 days
    at 4 different times of the day
    id: an int
    returns an ordered dict with weather forecast information
    '''
    # create Forecaster object
    fc = owm.three_hours_forecast_at_id(id)
    days = collections.OrderedDict()
    # start with today
    d = date.today()
    for i in range(4):
        days[(str(d))] = []
        d = d + timedelta(1)
    times = [" 6:00:00+00", " 12:00:00+00", " 18:00:00+00", " 23:59:59+00"]
    for key in days.keys():
        for t in times:
            try:
                # append to current key the weather object for specific time
                days[key].append(fc.get_weather_at(key+t))
            # raises error if time is out of range
            # e.g. getting today's weather at 12 o'clock when current time is past 12
            except NotFoundError:
                pass
    return days

