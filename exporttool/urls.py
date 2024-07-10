from django.urls import path
from .views import index, export_data, about, filterhelp

urlpatterns = [
    path('', index, name='index'),
    path('export_data/', export_data, name='export_data'),
    path('about/', about, name='about'),
    path('filterhelp/', filterhelp, name='filterhelp'),
]
