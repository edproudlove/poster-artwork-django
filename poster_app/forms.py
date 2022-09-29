from django import forms
from django.contrib.auth.models import User
from .models import Artist


class ArtistUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta():
        model = User
        fields = ('username','email','password')


class ArtistUserProfileInfoForm(forms.ModelForm):
    class Meta():
        model = Artist
        fields = ('name','profile_pic', 'location')