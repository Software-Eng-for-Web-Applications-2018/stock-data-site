# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


from flask_admin.contrib import sqla
from secure_views import SecureModelView


class StockPriceView(SecureModelView):

    can_create = False
    can_edit = False
    can_delete = False

    column_list = ('dateid', 'sym', 'volume', 'close', 'high', '_open', 'low')
    column_searchable_list = ('dateid', 'sym')
    column_filters = column_list
    column_labels = {'dateid': 'Date', 'sym': 'Symbol'}
    column_default_sort = ('dateid', 'sym')
    column_sortable_list = column_list
