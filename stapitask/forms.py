from django import forms

class searchbar(forms.Form):
    search = forms.CharField(max_length=1000)