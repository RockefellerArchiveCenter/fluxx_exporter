from django.core.exceptions import ValidationError
from django.forms import ClearableFileInput, FileField, Form
from django.forms.models import (BaseInlineFormSet, ModelForm,
                                 inlineformset_factory)

from .models import ExportJob, Field, Filter, Table


class TableFieldFormset(inlineformset_factory(
        Table,
        Field,
        fields=('id', 'include_in_export',),
        extra=0,
        can_delete=False,
        fk_name='table')):

    def get_queryset(self, *args, **kwargs):
        return super(TableFieldFormset, self).get_queryset().order_by('name')


class BaseTablesWithFields(BaseInlineFormSet):

    def get_queryset(self):
        if self.instance.id:
            queryset = Table.objects.filter(export_job=self.instance)
        else:
            queryset = Table.objects.filter(export_job__isnull=True)
        return queryset

    def add_fields(self, form, index):
        super().add_fields(form, index)

        form.nested = TableFieldFormset(
            instance=form.instance,
            data=form.data if form.is_bound else None,
            files=form.files if form.is_bound else None,
            prefix=f"tablefield-{form.prefix}-{TableFieldFormset.get_default_prefix()}")

    def clean(self):
        """Custom validation to ensure correct export of fields and tables."""

        super().clean()

        for form in self.forms:
            if form.instance.include_in_export:
                if hasattr(form, "nested"):
                    if not any([c.instance.include_in_export for c in form.nested]):
                        form.add_error(None, 'You must add at least one field to this table.')

    def is_valid(self):
        """Validate the nested formsets."""

        result = super().is_valid()

        if self.is_bound:
            for form in self.forms:
                if hasattr(form, "nested"):
                    result = result and form.nested.is_valid()

        return result

    def save(self, commit=True):
        """Save the nested formsets."""

        result = super().save(commit=commit)

        for form in self.forms:
            if hasattr(form, "nested"):
                form.nested.save(commit=commit)

        return result


ExportJobWithTables = inlineformset_factory(
    ExportJob,
    Table,
    formset=BaseTablesWithFields,
    fields=('id', 'include_in_export',),
    extra=0,
    can_delete=False
)


class FilterForm(ModelForm):
    class Meta:
        model = Filter
        fields = '__all__'

    def clean_field_name(self):
        """Ensure field name is in grant_request table."""
        data = self.cleaned_data['field_name']
        export_job = self.cleaned_data['export_job']
        grant_request_table = Table.objects.get(name='grant_request', export_job=export_job)
        grant_requested_fields = [field.name for field in Field.objects.filter(table=grant_request_table)]

        if data not in grant_requested_fields:
            raise ValidationError(f'"{data}" is not a field in the grant_request table.')

        return data


ExportJobWithFilters = inlineformset_factory(
    ExportJob,
    Filter,
    form=FilterForm,
    extra=2
)


class ExportJobForm(ModelForm):
    class Meta:
        model = ExportJob
        exclude = ('sftp_config',)
        help_texts = {
            'export_location': 'Path to the directory where exported records will be saved. \
                Path can be absolute, or relative to the Fluxx Exporter executable file. \
                Directory will be created if it does not exist.',
            'filter_string': 'Filter which grant records are exported using the format \
                "field name|relator|value". E.g. "grant_closed_at|range-year-cal|2010-2024". <br> \
                <a href="https://github.com/RockefellerArchiveCenter/fluxx_exporter/tree/base?tab=readme-ov-file#add-filters">See filter documentation</a> for more information.',
            'grant_ids': 'Comma-separated list of Fluxx grant IDs to export.',
        }


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(FileField):
    """Overrides FileField to handle multiple files."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class ImportTablesForm(Form):
    """Form for importing tables and fields from API documentation."""
    grant_request_file = FileField(label="Grant Request HTML file")
    related_tables_files = MultipleFileField(label="Related Tables HTML files", required=False)
