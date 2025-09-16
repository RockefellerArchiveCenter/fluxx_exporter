from django.urls import path, re_path

from .views import (AboutView, CreateExportJobView, DeleteExportJobView,
                    ExportJobView, FluxxConfigCreateView,
                    FluxxConfigDeleteView, FluxxConfigUpdateView,
                    FluxxConfigView, ImportTablesView, IndexView,
                    RunExportJobView, UpdateExportJobView)

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('about/', AboutView.as_view(), name='about'),
    path('import/', ImportTablesView.as_view(), name='import'),
    re_path(r'^export_job/$', CreateExportJobView.as_view(), name='exportjob_create'),
    re_path(r'^export_job/(?P<pk>\d+)/$', ExportJobView.as_view(), name='exportjob_detail'),
    re_path(r'^export_job/(?P<pk>\d+)/edit', UpdateExportJobView.as_view(), name='exportjob_update'),
    re_path(r'^export_job/(?P<pk>\d+)/delete', DeleteExportJobView.as_view(), name='exportjob_delete'),
    re_path(r'^export_job/(?P<pk>\d+)/run', RunExportJobView.as_view(), name='exportjob_run'),
    re_path(r'^fluxx_config/$', FluxxConfigCreateView.as_view(), name='fluxxconfig_create'),
    re_path(r'^fluxx_config/(?P<pk>\d+)/$', FluxxConfigView.as_view(), name='fluxxconfig_detail'),
    re_path(r'^fluxx_config/(?P<pk>\d+)/edit', FluxxConfigUpdateView.as_view(), name='fluxxconfig_update'),
    re_path(r'fluxx_config/(?P<pk>\d+)/delete', FluxxConfigDeleteView.as_view(), name='fluxxconfig_delete'),
]
