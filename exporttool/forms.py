'''
from django import forms
from .models import Entities

class EntitiesForm(forms.ModelForm):
    class Meta:
        model = Entities
        fields = '__all__'
'''