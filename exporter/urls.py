from django.urls import path

from .views import about, export_data, filterhelp, index

urlpatterns = [
    path('', index, name='index'),
    path('export_data/', export_data, name='export_data'),
    path('about/', about, name='about'),
    path('filterhelp/', filterhelp, name='filterhelp'),
]
