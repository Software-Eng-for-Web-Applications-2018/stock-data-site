# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


import datetime
import json
from app import db
from flask import (abort, request, url_for, redirect, flash, current_app)
from flask_admin import (BaseView, expose)
from flask_login import (current_user, login_user)
from models import StockPriceMinute


class JSONView(BaseView):

    empty_json = '{"dateid": [], "close": []}'

    def is_visible(self):
        return False

    def read_file(self, sym):
        try:
            with open('./predictions/{}.json'.format(sym), 'r') as f:
                data = f.read()
            return data
        except Exception as e:
            return self.empty_json

    @expose('/', methods=('GET',))
    def index(self):
        return self.empty_json

    @expose('/<sym>', methods=('GET',))
    def get_test(self, sym):
        sym_results = db.session.query(StockPriceMinute.sym).distinct().all()
        valid_syms = ['test'] + [val.sym.lower() for val in sym_results]
        if sym not in valid_syms:
            print('Invalid symbol, valid symbols are {}'.format(valid_syms))
            return abort(404)
        return self.read_file(sym)
