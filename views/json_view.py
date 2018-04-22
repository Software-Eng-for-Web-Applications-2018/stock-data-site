# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


import datetime
import json
from app import db
from config import POST_PASSWD
from flask import (abort, request, url_for, redirect, flash, current_app)
from flask_admin import (BaseView, expose)
from flask_login import (current_user, login_user)
from models import StockPriceMinute


class JSONView(BaseView):

    empty_json = '{"dateid": [], "close": []}'

    def is_visible(self):
        return False

    def valid_passwd(self, passwd):
        return passwd == POST_PASSWD

    def read_file(self, sym):
        try:
            with open('./predictions/{}.json'.format(sym), 'r') as f:
                data = f.read()
            return data
        except Exception as e:
            return self.empty_json

    def valid_predictions(self, data):
        try:
           assert len(data['dateid']) == len(data['close'])
        except AssertionError:
            return False
        return True

    @expose('/', methods=('GET',))
    def index(self):
        return self.empty_json

    @expose('/<sym>', methods=('GET', 'POST'))
    def sym_handle(self, sym):
        if request.method == 'POST':
            # Read POST request
            passwd = request.form['passwd']
            sym = request.form['sym'].lower()
            predictions = request.form['predictions']

            # Validate password
            if not self.valid_passwd(passwd):
                print('Invalid password')
                return abort(403)

            # Validate symbol
            sym_results = db.session.query(StockPriceMinute.sym).distinct().all()
            valid_syms = ['test'] + [val.sym.lower() for val in sym_results]
            if sym not in valid_syms:
                print('Invalid symbol, valid symbols are {}'.format(valid_syms))
                return abort(400)

            # Validate prediction data
            try:
                data = json.loads(predictions)
            except Exception as e:
                print(e)
                return abort(400)
            if not(self.valid_predictions(data)):
                print('Invalid data format')
                return abort(400)

            # TODO: Overwrite json with posted data
            with open('./predictions/' + sym + '.json', 'w') as f:
                f.write(json.dumps(data))

            return '200'
        else:
            sym_results = db.session.query(StockPriceMinute.sym).distinct().all()
            valid_syms = ['test'] + [val.sym.lower() for val in sym_results]
            if sym not in valid_syms:
                print('Invalid symbol, valid symbols are {}'.format(valid_syms))
                return abort(404)
            return self.read_file(sym)
