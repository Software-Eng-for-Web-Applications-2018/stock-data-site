from app import db
from models import User
from views.home_view import HomeView
from views.login_view import LoginView
from views.logout_view import LogoutView
from views.user_view import UserView


def add_admin_views(admin, app):
    # Home View
    admin.add_view(HomeView(name='Home', endpoint='home'))

    # User dash view handling
    #admin.add_view(DashView(name='User Portal', endpoint='userdash',
    #               app=app))
    #admin.add_view(BusinessDashView(name='Business Portal',
    #                                endpoint='businessdash', app=app))

    # Admin portal views
    admin.add_view(UserView(User, db.session, name='Users'))
    #admin.add_view(HazardSummaryView(
    #    HazardSummary, db.session, name='Hazard Summary'))
    #admin.add_view(HazardLocationView(
    #    HazardLocation, db.session, name='Hazard Locations'))

    # Login and Logout views
    admin.add_view(LoginView(name='Login', endpoint='login'))
    admin.add_view(LogoutView(name='Logout', endpoint='logout'))
