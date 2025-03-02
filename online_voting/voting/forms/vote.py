from django import forms
from ..models import Vote

class VoteForm(forms.ModelForm):
    class Meta:
        model = Vote
        fields = ['candidate', 'is_anonymous']
        widgets = {
            'candidate': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }