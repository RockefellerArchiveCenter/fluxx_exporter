import re

from bs4 import BeautifulSoup
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, FormView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .exporters import Exporter
from .forms import ExportJobForm, ExportJobWithTables, ImportTablesForm
from .models import ExportJob, Field, Table


class IndexView(TemplateView):
    template_name = 'exporter/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_jobs"] = ExportJob.objects.all()
        return context


class AboutView(TemplateView):
    template_name = 'exporter/about.html'


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
        """Creates Table objects and associates them with the export job."""
        context = self.get_context_data(form=form)
        tables_formset = context['formset']
        if tables_formset.is_valid():
            response = super().form_valid(form)
            for form in tables_formset:
                new_table, _ = Table.objects.get_or_create(
                    name=form.instance.name,
                    include_in_export=form.instance.include_in_export,
                    export_job=self.object)
                for field in form.nested:
                    related_table = None
                    if field.instance.related_table:
                        related_table, _ = Table.objects.get_or_create(
                            name=field.instance.related_table.name,
                            export_job=self.object
                        )
                    Field.objects.create(
                        name=field.instance.name,
                        include_in_export=field.instance.include_in_export,
                        related_table=related_table,
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


class ImportTablesView(FormView):
    template_name = 'exporter/import_form.html'
    form_class = ImportTablesForm
    success_url = reverse_lazy('index')  # TODO

    def form_valid(self, form):
        try:
            grant_request_file = form.cleaned_data['grant_request_file']
            related_tables_files = form.cleaned_data['related_tables_files']
            related_tables_dict = self.get_related_tables_dict(related_tables_files)
            table_name, grant_request_data = self.get_table_data(grant_request_file)
            if table_name != 'grant_request':
                raise Exception(f"The file {grant_request_file} does not contain GrantRequest data.")
            table, _ = Table.objects.get_or_create(name='grant_request', export_job=None)
            for row in grant_request_data:
                self.handle_row(row, table, related_tables_dict)
            table_len = len(related_tables_files) + 1
            messages.add_message(
                self.request,
                messages.SUCCESS,
                f'{table_len} {"table" if table_len == 1 else "tables"} imported successfully.')
            return super().form_valid(form)
        except Exception as e:
            messages.add_message(self.request, messages.ERROR, mark_safe(f'Import encountered an error.<br/><br/>{e}'))
            return super().form_invalid(form)

    def get_related_tables_dict(self, related_tables_files):
        related_tables_dict = {}
        for related_table in related_tables_files:
            title, data = self.get_table_data(related_table)
            related_tables_dict[title] = data
        return related_tables_dict

    def get_normalized_title(self, raw_title):
        try:
            split_title = re.findall('[A-Z][^A-Z]*', raw_title)
            return '_'.join([seg.lower() for seg in split_title])
        except Exception as e:
            raise Exception(f'Encountered error when parsing document title from {raw_title}: {e}')

    def get_table_data(self, html):
        """Parses HTML file and returns table data.

        Args:
            html (file object): File object containing HTML data

        Returns:
            table_data (dict): Parsed table data.
        """
        try:
            doc = BeautifulSoup(html, features="html.parser")
            raw_title = doc.find('h2').text
            table_title = self.get_normalized_title(raw_title)
            table = doc.find("table")
            rows = table.findAll('tr')
            headers = [th.text.strip() for th in rows[0].findAll('th')]
            table_data = []
            for row in rows[1:]:
                parsed_row = [td.text.strip().rstrip('*') for td in row.findAll('td')]
                row_dict = {}
                for idx, key in enumerate(headers):
                    row_dict[key] = parsed_row[idx]
                table_data.append(row_dict)
            return table_title, table_data
        except Exception as e:
            raise Exception(f'Encountered error when parsing data from {html}: {e}')

    def row_is_relation(self, row):
        """Determine if row represents a related table

        Args:
            row (dict): row of data from table.

        Returns:
            is_relation (bool): row represents database relation.
        """
        return bool(row['type'] == 'relation' and row['related_class'])

    def row_is_field(self, row):
        """Determine if row represents a field

        Args:
            row (dict): row of data from table.

        Returns:
            is_relation (bool): row represents field.
        """
        return bool(row['type'] and row['type'] != 'relation')

    def parse_related_table_name(self, row):
        """Generate normalized table name.

        Args:
            row (dict): row of data from table.

        Returns:
            parsed (str): parsed related table name.
        """
        parsed = re.findall('[A-Z][^A-Z]*', row['related_class'])
        return "_".join([s.lower() for s in parsed])

    def handle_row(self, row, table, related_tables, resolve=True):
        """Recursively process rows, adding related entities.

        Args:
            row (dict): row of HTML table.
            table (Table instance): parent table with which Fields are associated.
            related_tables (dict): dictionary of table data identified by key.
            resolve (bool): resolve related tables.
        """
        if self.row_is_relation(row) and resolve:
            related_table_name = self.parse_related_table_name(row)
            if related_tables.get(related_table_name):
                related_table_data = related_tables[related_table_name]
                related_table, _ = Table.objects.get_or_create(name=related_table_name)
                Field.objects.get_or_create(name=row['name'], table=table, related_table=related_table)
                for row in related_table_data:
                    self.handle_row(row, related_table, related_tables, resolve=False)  # Relations are only resolved one level deep
        elif self.row_is_field(row):
            Field.objects.get_or_create(name=row['name'], table=table)
