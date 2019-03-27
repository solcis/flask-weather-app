# flask-weather-app


#### What is flask-weather-app?
A SQLite and Flask powered weather application written in Python 2.7. Not compatible with Python 3 at the moment.

#### What do I need to run the application?
Assuming you already have Flask installed, if not [go here](http://flask.pocoo.org/) or if you don't feel like reading just run this command:

`pip install -U Flask`

*Use of virtualenv is encouraged.*

You also need an OpenWeatherMap API key. You can get it [here](http://openweathermap.org/appid#get).

And [PyOWM](https://github.com/csparpa/pyowm) library:

`pip install pyowm==2.3.2`


#### How do I use it?

1. *edit the configuration in the flask_weather_app.py file.*
2. *tell flask about the right application:*

  *Open up your terminal and export* `FLASK_APP` *enviroment variable:* `export FLASK_APP=flask_weather_app.py`
  
  *For Windows use set instead of export.*
  
3. *Fire up a shell and run this:*

  `flask initdb`
  
  *Alternatively you can use* `python -m flask initdb`
  
4. *now you can run the app:*

  `flask run` *or* `python -m flask run`
  
  *The application will greet you at*
  
  `http://localhost:5000/`
 
