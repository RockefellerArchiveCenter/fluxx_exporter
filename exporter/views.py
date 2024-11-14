from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .exporters import Exporter
from .forms import ExportJobForm, ExportJobWithTables
from .models import ExportJob, Field, Table


class IndexView(TemplateView):
    template_name = 'exporter/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_jobs"] = ExportJob.objects.all()
        return context


class AboutView(TemplateView):
    template_name = 'exporter/about.html'


class FilterHelpView(TemplateView):
    template_name = 'exporter/filterhelp.html'


class ExportJobView(DetailView):
    model = ExportJob


class CreateExportJobView(CreateView):
    model = ExportJob
    template_name = 'exporter/exportjob_form.html'
    form_class = ExportJobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = ExportJobWithTables(**self.get_form_kwargs())
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        tables_formset = context['formset']
        if tables_formset.is_valid():
            response = super().form_valid(form)
            for form in tables_formset:
                new_table = Table.objects.create(
                    name=form.instance.name,
                    include_in_export=form.instance.include_in_export,
                    export_job=self.object)
                for field in form.nested:
                    Field.objects.create(
                        name=field.instance.name,
                        include_in_export=field.instance.include_in_export,
                        table=new_table)
            return response
        else:
            return super().form_invalid(form)


class UpdateExportJobView(UpdateView):
    model = ExportJob
    template_name = 'exporter/exportjob_form.html'
    form_class = ExportJobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = ExportJobWithTables(**self.get_form_kwargs())
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        tables_formset = context['formset']
        if tables_formset.is_valid():
            tables_formset.save()
            return super().form_valid(form)
        else:
            return super().form_invalid(form)


class DeleteExportJobView(DeleteView):
    model = ExportJob
    success_url = reverse_lazy('index')


class RunExportJobView(DetailView):
    model = ExportJob

    def get(self, request, *args, **kwargs):
        export_job_id = int(request.get_full_path().rstrip('/').split('/')[-2])
        result, error = Exporter(export_job_id).fluxx_export()
        if result:
            messages.add_message(request, messages.SUCCESS, 'Export completed successfully.')
        else:
            messages.add_message(request, messages.ERROR, mark_safe(f'Export encountered an error.<br/><br/>{error}'))
        return super().get(request, *args, **kwargs)
