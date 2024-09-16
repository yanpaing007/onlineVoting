from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import *


class VotingEventForm(forms.ModelForm):
    class Meta:
        model = VotingEvent
        fields = ['event_name', 'start_time', 'end_time','categories', 'candidate_numbers', 'is_private']
        widgets = {
            'event_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'categories': forms.CheckboxSelectMultiple(),
            'candidate_numbers': forms.NumberInput(attrs={'class': 'form-control'})
        }


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'description', 'profile_pic']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True


class VoteForm(forms.ModelForm):
    class Meta:
        model = Vote
        fields = ['candidate', 'is_anonymous']
        widgets = {
            'candidate': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'is_anonymous' : forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }



class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    name = forms.CharField(required=True, max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'password1', 'password2']

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'aria-label': 'Username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'aria-label': 'Password',
        })
    )
    
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
        
