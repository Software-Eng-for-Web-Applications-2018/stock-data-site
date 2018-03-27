from app import db
from models import (StockPriceDay, StockPriceMinute, User)
from views.dash_view import DashView
from views.home_view import HomeView
from views.login_view import LoginView
from views.logout_view import LogoutView
from views.user_view import UserView
from views.stock_price_view import StockPriceView


def add_admin_views(admin, app):
    # Home View
    admin.add_view(HomeView(name='Home', endpoint='home'))

    # User dash view handling
    admin.add_view(DashView(
        name='Real-Time Portal',
        endpoint='realtimeportal',
        app=app
    ))
    admin.add_view(DashView(
        name='Historical Portal',
        endpoint='historicalportal',
        app=app
    ))

    # Model view handling
    admin.add_view(StockPriceView(
        StockPriceDay,
        db.session,
        name='Daily Stock Prices')
    )
    admin.add_view(StockPriceView(
        StockPriceMinute,
        db.session,
        name='Minute Stock Prices')
    )

    # Admin portal views
    admin.add_view(UserView(User, db.session, name='Users'))

    # Login and Logout views
    admin.add_view(LoginView(name='Login', endpoint='login'))
    admin.add_view(LogoutView(name='Logout', endpoint='logout'))
