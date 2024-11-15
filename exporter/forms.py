from django.forms import ValidationError
from django.forms.models import (BaseInlineFormSet, ModelForm,
                                 inlineformset_factory)

from .models import ExportJob, Field, Table

TableFieldFormset = inlineformset_factory(
    Table,
    Field,
    fields=('id', 'include_in_export',),
    extra=0,
    can_delete=False,
    fk_name='table')


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
                        raise ValidationError('You must add at least one field to this table.')

            else:
                if hasattr(form, "nested"):
                    if any([c.instance.include_in_export for c in form.nested]):
                        raise ValidationError('You cannot export fields without also exporting the parent table.')

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


class ExportJobForm(ModelForm):
    class Meta:
        model = ExportJob
        exclude = ('sftp_config',)
        help_texts = {
            'export_location': 'Directory in which exported records will be saved.'
        }
