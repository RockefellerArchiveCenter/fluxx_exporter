from django.urls import path, re_path

from .views import (AboutView, CreateExportJobView, DeleteExportJobView,
                    ExportJobRunView, ExportJobView, FilterHelpView, IndexView,
                    UpdateExportJobView)

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('about/', AboutView.as_view(), name='about'),
    path('filterhelp/', FilterHelpView.as_view(), name='filterhelp'),
    re_path(r'^export_job/$', CreateExportJobView.as_view(), name='exportjob_create'),
    re_path(r'^export_job/(?P<pk>\d+)/$', ExportJobView.as_view(), name='exportjob_detail'),
    re_path(r'^export_job/(?P<pk>\d+)/edit', UpdateExportJobView.as_view(), name='exportjob_update'),
    re_path(r'export_job/(?P<pk>\d+)/delete', DeleteExportJobView.as_view(), name='exportjob_delete'),
    re_path(r'export_job/(?P<pk>\d+)/run', ExportJobRunView.as_view(), name='exportjob_run'),
]
