from matplotlib import widgets
from . import models

from django import forms

class CreateListing(forms.ModelForm):
    class Meta:
        model = models.AuctionListing
        fields = ['title','description','image','starting_bid','category']
        labels = {
            'image' : 'Image (URL)'
        }


class PlaceBid(forms.ModelForm):

    class Meta:
        model = models.Bid
        fields = ['amount']  