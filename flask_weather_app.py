# -*- coding: utf-8 -*-
"""
    flask-weather-app
    ~~~~~~~~~~~~

    A weather application.
    Written with Flask and sqlite3. Uses pyowm library
    to get the weather information from OpenWeatherMap's API.

    :copyright: (2016) by solcis.
    :license: MIT, see LICENSE for more details.

"""

import os
from flask import Flask, request, render_template, g, jsonify
import pyowm, json, collections, sqlite3
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
    DATABASE=os.path.join(app.root_path, 'flask_weather_app.db'),
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
    Gets user's input from form and tries to
    get weather info  for current day and next 3 days
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

@app.route('/search/', methods=['GET'])
def search():
    '''
    Function that works together with Ajax requests to send suggestions as user types
    returns: data in json format
    '''
    db = get_db()
    value = request.args.get('city') + '%'
    # some entries are duplicated, we use distinct keyword to ignore them
    q = db.cursor().execute("select distinct city, country_code, lon, lat from cities where city like ? order by city, country_code", [value])
    res = [x for x in q]
    data = []
    for i in res:
        data.append({'label': i[0] + ' ' +  i[1], 'city': i[0], 'country_code': i[1]})
    return jsonify(json_data=data)

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
    data['icon'] = 'http://openweathermap.org/img/w/' + weather.get_weather_icon_name() + '.png'
    data['date'] = '{:%a, %d %B}'.format(date.today())
    return data

def get_forecast(id):
    '''
    Gets forecast for the next 3 days at 4 different times of the day
    id: an int
    returns an ordered dict with weather forecast information
    '''
    # create Forecaster object
    fc = owm.three_hours_forecast_at_id(id)
    days = collections.OrderedDict()
    d = date.today()
    for i in range(3):
        # add 1 day to d
        d = d + timedelta(1)
        # get date formatted and add it to dict
        date_f = '{:%A, %d %B}'.format(d)
        days[(str(d))] = [date_f,]
    times = [" 6:00:00+00", " 12:00:00+00", " 18:00:00+00", " 23:59:59+00"]
    for key in days.keys():
        for t in times:
            try:
                # append to current key a dict with the weather info for time t
                w = fc.get_weather_at(key+t)
                data = {}
                data['temp'] = w.get_temperature(unit='celsius')
                data['status'] = w.get_status()
                data['detail'] = w.get_detailed_status()
                data['icon'] = 'http://openweathermap.org/img/w/' + w.get_weather_icon_name() + '.png'
                days[key].append(data)
            # raises error if time is out of range
            # e.g. getting today's weather at 12 o'clock when current time is past 12
            except NotFoundError:
                pass
    return days
