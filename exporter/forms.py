from django.forms import ValidationError
from django.forms.models import (BaseInlineFormSet, ModelForm,
                                 inlineformset_factory)

from .models import Column, Entity, ExportJob

EntityColumnFormset = inlineformset_factory(
    Entity,
    Column,
    fields=('id', 'include_in_export',),
    extra=0,
    can_delete=False)


class BaseEntitiesWithColumns(BaseInlineFormSet):

    def get_queryset(self):
        if self.instance.id:
            queryset = Entity.objects.filter(export_job=self.instance)
        else:
            queryset = Entity.objects.filter(export_job__isnull=True)
        return queryset

    def add_fields(self, form, index):
        super().add_fields(form, index)

        form.nested = EntityColumnFormset(
            instance=form.instance,
            data=form.data if form.is_bound else None,
            files=form.files if form.is_bound else None)

    def clean(self):
        """Custom validation to ensure correct export of columns and entities."""

        super().clean()

        for form in self.forms:
            if form.instance.include_in_export:
                if hasattr(form, "nested"):
                    if not any([c.instance.include_in_export for c in form.nested]):
                        raise ValidationError('You must add at least one field to this column.')

            else:
                if hasattr(form, "nested"):
                    if any([c.instance.include_in_export for c in form.nested]):
                        raise ValidationError('You cannot export fields without also exporting the parent column.')

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


ExportJobWithEntities = inlineformset_factory(
    ExportJob,
    Entity,
    formset=BaseEntitiesWithColumns,
    fields=('id', 'include_in_export',),
    extra=0,
    can_delete=False
)


class ExportJobForm(ModelForm):
    class Meta:
        model = ExportJob
        fields = '__all__'
