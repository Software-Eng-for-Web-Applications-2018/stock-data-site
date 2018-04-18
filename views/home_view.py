# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


from flask_admin import (BaseView, expose)


class HomeView(BaseView):

    def is_visible(self):
        return False

    @expose('/', methods=('GET',))
    def index(self):
        return self.render('home.html')
