from app import db


class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(320), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    user_group = db.Column(db.String(50), nullable=True)
    active = db.Column(db.Boolean, nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    last_login_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return 'Email: %s' % self.email

    def is_active(self):
        return self.active

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

    def is_anonymous(self):
        return False

    def has_role(self, role):
        return self.user_group == role


class StockPriceDay(db.Model):

    __tablename__ = 'stock_price_day'

    dateid = db.Column(db.Date, primary_key=True)
    sym = db.Column(db.String(5), primary_key=True)
    volume = db.Column(db.Float)
    close = db.Column(db.Float)
    high = db.Column(db.Float)
    _open = db.Column('open', db.Float)
    low = db.Column(db.Float)


class StockPriceMinute(db.Model):

    __tablename__ = 'stock_price_minute'

    dateid = db.Column(db.DateTime, primary_key=True)
    sym = db.Column(db.String(5), primary_key=True)
    volume = db.Column(db.Float)
    close = db.Column(db.Float)
    high = db.Column(db.Float)
    _open = db.Column('open', db.Float)
    low = db.Column(db.Float)
