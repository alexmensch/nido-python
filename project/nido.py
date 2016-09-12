import sqlite3
from contextlib import closing
from enum import Enum
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from validate_email import validate_email
from lib.CollectData import Sensor, LocalWeather
from config import NidoConfig

# Configuration
cfg = NidoConfig().get_config()
DEBUG = cfg['flask']['debug']
SECRET_KEY = cfg['flask']['secret_key']

# Initialize the application
#
app = Flask(__name__)
app.config.from_object(__name__)

# Define some custom exception handling
#
class NidoDatabaseError(Exception):
    """ Some kind of error in our database; data validation problem """
    pass

# Define some enums
#
class Mode(Enum):
    off = 0
    heat = 1
    cool = 2
    heat_cool = 3

_MODE_NAME = {
        Mode.off: 'Off',
        Mode.heat: 'Heat',
        Mode.cool: 'Cool',
        Mode.heat_cool: 'Heat/Cool'
        }

class Status(Enum):
    off = 0
    heating = 1
    cooling = 2

_STATUS_NAME = {
        Status.off: 'Off',
        Status.heating: 'Heating',
        Status.cooling: 'Cooling'
        }

# SQLite3 database functions
#
def connect_db():
    db = sqlite3.connect(cfg['db']['database'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource(cfg['db']['schema'], mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False, db=None):
    if db == None:
        db = g.db
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# Set up common request functions to make database connection available
#
@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# Application routes
#
@app.route('/set_config', methods=['POST', 'GET'])
def set_config():
    error = None
    if not session.get('logged_in'):
        abort(401)

    if request.method == 'POST':
        if request.form['zipcode'] is None:
            error = 'Missing Zipcode'
        elif request.form['user_location_name'] is None:
            error = 'Missing thermostat location name'
        elif request.form['set_temp'] is None:
            error = 'No temperature set point provided'
        else:
            # Single user system :)
            user_id = 1
            auto_location_name = LocalWeather(request.form['zipcode']).conditions['location_name']
            set_values = [
                    user_id,
                    int(request.form['zipcode']),
                    int(request.form['celsius']),
                    request.form['user_location_name'],
                    auto_location_name,
                    int(request.form['mode']),
                    int(request.form['set_temp'])
                    ]
            if query_db('select * from config where user_id = 1', one=True):
                g.db.execute('update config set user_id = ?, zipcode = ?, celsius = ?, user_location_name = ?, auto_location_name = ?, mode = ?, set_temp = ? where user_id = 1', set_values)
            else:
                g.db.execute('insert into config (user_id, zipcode, celsius, user_location_name, auto_location_name, mode, set_temp) values (?, ?, ?, ?, ?, ?, ?)', set_values)
            g.db.commit()
            flash('Settings saved')
            return redirect(url_for('show_config'))
    return render_template('new_config.html', error=error, mode=Mode, mode_name=_MODE_NAME)

@app.route('/config')
def show_config():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    user_config = query_db('select * from users join config on users.user_id = config.user_id', one=True)
    if user_config:
        return render_template('show_config.html', user_config=user_config, mode=Mode(user_config['mode']), mode_name=_MODE_NAME)
    elif query_db('select * from users', one=True):
        return redirect(url_for('set_config'))
    return redirect(url_for('show_status'))

@app.route('/add_user', methods=['POST'])
def add_user():
    error = None
    if not session.get('logged_in'):
        abort(401)

    if request.form['name'] is None:
        error = 'Missing name'
    elif validate_email(request.form['email'], verify=True) is False:
        error = 'Invalid email address'
    else:
        g.db.execute('insert into users (name, email) values (?, ?)', [request.form['name'], request.form['email']])
        g.db.commit()
        flash('New user successfully created')
        return redirect(url_for('show_config'))
    return render_template('new_user.html', error=error)

@app.route('/')
def show_status():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    user = query_db('select * from users', one=True)
    if user:
        user_config = query_db('select * from users join config on users.user_id = config.user_id', one=True)
        if user_config is None:
            flash('Please configure Nido to continue')
            return redirect(url_for('set_config'))
        # Get current weather and sensor data
        if user_config['celsius'] == 1:
            celsius_setting = True
        elif user_config['celsius'] == 0:
            celsius_setting = False
        else:
            raise NidoDatabaseError('Invalid Boolean value in database for Celsius setting')
        sensor = Sensor(celsius=celsius_setting)
        weather = LocalWeather(zipcode=user_config['zipcode'], celsius=celsius_setting)
        # Round up readings to whole numbers
        sensor.conditions['relative_humidity'] = int(round(sensor.conditions['relative_humidity']))
        sensor.conditions['temp'] = int(round(sensor.conditions['temp']))
        weather.conditions['temp'] = int(round(weather.conditions['temp']))
        return render_template('show_status.html', sensor=sensor.conditions, weather=weather.conditions, user_config=user_config, celsius_setting=celsius_setting, mode=Mode(user_config['mode']), mode_name=_MODE_NAME, status=Status(user_config['status']), status_name=_STATUS_NAME)
    return render_template('new_user.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Need to modify this section to take it from the users table
        if request.form['username'] != cfg['flask']['username']:
            error = 'Invalid username'
        elif request.form['password'] != cfg['flask']['password']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_status'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=cfg['flask']['port'])
