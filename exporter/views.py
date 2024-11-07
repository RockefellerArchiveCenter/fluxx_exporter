from django.urls import reverse_lazy
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .exporters import Exporter
from .forms import ExportJobForm, ExportJobWithEntities
from .models import Column, Entity, ExportJob


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
        context['formset'] = ExportJobWithEntities(**self.get_form_kwargs())
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        entities_formset = context['formset']
        if entities_formset.is_valid():
            response = super().form_valid(form)
            for form in entities_formset:
                # TODO handle related_entity
                new_entity = Entity.objects.create(
                    name=form.instance.name,
                    include_in_export=form.instance.include_in_export,
                    export_job=self.object)
                for column in form.nested:
                    Column.objects.create(
                        name=column.instance.name,
                        include_in_export=column.instance.include_in_export,
                        entity=new_entity)
            return response
        else:
            return super().form_invalid(form)


class UpdateExportJobView(UpdateView):
    model = ExportJob
    template_name = 'exporter/exportjob_form.html'
    form_class = ExportJobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = ExportJobWithEntities(**self.get_form_kwargs())
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        entities_formset = context['formset']
        if entities_formset.is_valid():
            entities_formset.save()
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
        Exporter(export_job_id).fluxx_export()
        return super().get(request, *args, **kwargs)
