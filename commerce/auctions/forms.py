from cProfile import label
from matplotlib import widgets
from . import models

from django import forms

# Form to create listing
class CreateListing(forms.ModelForm):
    class Meta:
        error_css_class = 'error'
        model = models.AuctionListing
        fields = ['title','description','image','starting_bid','category']
        labels = {
            'image' : 'Image (URL)'
        }

# Form to place bid
class PlaceBid(forms.ModelForm):
    class Meta:
        error_css_class = 'error'
        model = models.Bid
        fields = ['amount'] 
        labels ={ 'amount': 'Enter Bid amount'}

class MakeComment(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ['content']
        widgets = {
            'content' : forms.Textarea(attrs={'placeholder': 'Leave a Comment','rows': 2, 'cols': 100,'class': 'comment-textarea'})
        }
        
        labels = {'content': ''}
