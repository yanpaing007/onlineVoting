from django import forms
from django.contrib.auth.models import User
from ..models import Profile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'birthday', 'timezone']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
        }