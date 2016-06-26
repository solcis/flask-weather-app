# This Python file uses the following encoding: utf-8
import os
import flask_weather_app
import unittest
import tempfile


class FlaskWeatherAppTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, flask_weather_app.app.config['DATABASE'] = tempfile.mkstemp()
        flask_weather_app.app.config['TESTING'] = True
        self.app = flask_weather_app.app.test_client()
        with flask_weather_app.app.app_context():
            flask_weather_app.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(flask_weather_app.app.config['DATABASE'])

    def test_index(self):
        rv = self.app.get('/')
        assert rv.status == '200 OK'

    def input_for_form(self, city, code):
        return self.app.post('/weather', data=dict(
            city=city,
            country_code=code
        ), follow_redirects=True)

    def test_form(self):
        cities = [['Milan', 'It'], ['Évry', 'Fr'], ['Lima', 'Pe'], ['Buenos Aires', 'Ar']]
        for city in cities:
            rv = self.input_for_form(city[0], city[1])
            assert city[0] in rv.data


if __name__ == '__main__':
    unittest.main()
