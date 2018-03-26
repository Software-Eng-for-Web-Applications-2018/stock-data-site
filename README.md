# Stock Data Site
Dashboard for predicted stock values.

## Installation
- Runs with Python3.5.2

### Pip

#### Linux
`apt-get install pip3`

#### Windows
- I recommend using Anaconda for Python 3 or Cygwin
- Anaconda will have pip3 already installed
- Cygwin select "pip3" binary to install along with "python3.5"

## Configuration
- Change the name of "example_config.py" to config.py"
- Set the SECRET_KEY value
- Set SQL_DB_URI string
  * <http://flask-sqlalchemy.pocoo.org/2.3/config/>

### Python Libraries
- `pip3 install -r requirements.txt`

## Running
Run site on localhost:5000.
- `python3 main.py 5000`
