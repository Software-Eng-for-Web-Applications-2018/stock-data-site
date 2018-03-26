'''example_config.py

Example config.py file containing sensitive information
'''


# SQL Alchemy SQL URI
# http://flask-sqlalchemy.pocoo.org/2.3/config/
MYSQL_DB_URI = '<flavor>://<user>:<password>@<host>:<port>/<db>'


# Secrety key for crypto exchange
# Generate this key yourself:
#     python3
#     import os
#     os.urandom(24)
#
# For more info visit http://flask.pocoo.org/docs/0.12/quickstart/
SECRET_KEY = 'Paste the generate value here!'
