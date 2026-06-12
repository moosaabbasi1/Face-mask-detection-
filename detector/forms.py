from django import forms
from .models import ContactMessage


class ImageUploadForm(forms.Form):
    image = forms.ImageField(
        label='Upload Image',
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control',
            'id':    'imageUpload',
        })
    )


class CameraForm(forms.Form):
    """Receives a base-64 encoded frame from the webcam JS."""
    image_data = forms.CharField(widget=forms.HiddenInput())


class ContactForm(forms.ModelForm):
    class Meta:
        model  = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email':   forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5,
                                             'placeholder': 'Write your message…'}),
        }