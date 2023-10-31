from tkinter import CASCADE
from django.contrib.auth.models import AbstractUser
from django.db import models
from matplotlib import category


class User(AbstractUser):
    pass

#Class to store the category details
class Category(models.Model):
    categoryName = models.CharField(max_length=64)

# Class to store the auction listing details
class AuctionListing(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    image = models.URLField()
    price = models.DecimalField(decimal_places=2,max_digits=10)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,blank=True)
    isActive = models.BooleanField()
    seller = models.ForeignKey(User,on_delete=models.CASCADE)

#Class to store the bid details
class Bid(models.Model):
    bidder = models.ForeignKey(User,on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2,max_digits=10)
    listing = models.ForeignKey(AuctionListing,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

#Class to store the comment details
class Comment(models.Model):
    commenter  = models.ForeignKey(User,on_delete=models.CASCADE)
    listing = models.ForeignKey(AuctionListing,on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)