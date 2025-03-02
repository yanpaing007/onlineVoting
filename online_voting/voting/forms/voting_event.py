from django import forms
from ..models import VotingEvent

class VotingEventForm(forms.ModelForm):
    class Meta:
        model = VotingEvent
        fields = ['event_name', 'start_time', 'end_time', 'categories', 'candidate_numbers', 'is_private']
        widgets = {
            'event_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'categories': forms.CheckboxSelectMultiple(),
            'candidate_numbers': forms.NumberInput(attrs={'class': 'form-control'})
        }