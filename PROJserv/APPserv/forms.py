from django import forms
from .models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['code', 'title', 'category', 'base_price', 'standard_duration_minutes']