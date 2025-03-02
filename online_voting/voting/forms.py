from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Div, Submit
from .models import *


class VotingEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('event_name', css_class='textinput'),
                css_class='col-span-2'
            ),
            Div(
                Field('start_time', css_class='datetimeinput'),
                Field('end_time', css_class='datetimeinput'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-6'
            ),
            Div(
                Field('categories', template='voting/custom_checkbox_select.html'),
                css_class='col-span-2 space-y-2'
            ),
            Div(
                Field('candidate_numbers', css_class='numberinput'),
                Field('is_private', template='voting/custom_checkbox.html'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-6'
            ),
        )

    class Meta:
        model = VotingEvent
        fields = ['event_name', 'start_time', 'end_time', 'categories', 'candidate_numbers', 'is_private']
        widgets = {
            'event_name': forms.TextInput(attrs={
                'class': 'textinput',
                'placeholder': 'Enter event name'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'datetimeinput',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'datetimeinput',
                'type': 'datetime-local'
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'checkboxinput'
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'checkboxinput'
            }),
            'candidate_numbers': forms.NumberInput(attrs={
                'class': 'numberinput',
                'min': '2',
                'placeholder': 'Minimum 2 candidates'
            })
        }


class CandidateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='textinput'),
            Field('description', css_class='textarea'),
            Field('profile_pic', css_class='fileinput'),
        )

    class Meta:
        model = Candidate
        fields = ['name', 'description', 'profile_pic']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'textinput',
                'placeholder': 'Enter candidate name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 3,
                'placeholder': 'Enter candidate description'
            }),
            'profile_pic': forms.FileInput(attrs={
                'class': 'fileinput',
                'accept': 'image/*'
            }),
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
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400 transition-colors',
            'placeholder': 'Email address'
        })
    )
    name = forms.CharField(
        required=True, 
        max_length=100, 
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400 transition-colors',
            'placeholder': 'Full name'
        })
    )
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400 transition-colors',
            'placeholder': 'Choose a username'
        })
    )
    password1 = forms.CharField(
        label='Password', 
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400 transition-colors',
            'placeholder': 'Create a password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password', 
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400 transition-colors',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
        return user


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

