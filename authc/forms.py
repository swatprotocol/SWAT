
from django import forms
from django.utils.safestring import mark_safe
from captcha.fields import ReCaptchaField

class UpdateCanvasForm(forms.Form):
    email = forms.EmailField(required=True)
    fingerprint = forms.CharField(max_length=100,
            required=True)
    canvasURL = forms.CharField()
    version = forms.IntegerField()

class CheckFpForm(forms.Form):
    email = forms.EmailField(required=True)
    fingerprint = forms.CharField(max_length=100,
            required=True)

class RegisterForm(forms.Form):
    email = forms.EmailField(required=True)
    captcha = ReCaptchaField()
    #XXX Todo add captcha
class LoginForm(forms.Form):
    #pseudo = forms.CharField(label='Username', max_length=30, required=True)
    email = forms.EmailField(required=True)
    #password = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    #confPassword = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=True)
