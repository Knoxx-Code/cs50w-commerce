from . import models

from django import forms

class CreateListing(forms.ModelForm):
    class Meta:
        model = models.AuctionListing
        fields = {'title','description','image','starting_bid','category','status','seller'}