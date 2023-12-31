

from django.contrib.auth.models import AbstractUser
from django.db import models



class User(AbstractUser):
    pass

#Class to store the category details
class Category(models.Model):
    categoryName = models.CharField(max_length=64)

    def __str__(self):
        return self.categoryName

# Class to store the auction listing details
class AuctionListing(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    image = models.URLField(blank=True)
    starting_bid = models.DecimalField(decimal_places=2,max_digits=10)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,blank=True)
    status = models.CharField(
    max_length=10,
    choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('disabled', 'Disabled'),
    ],
    default='active'
    )

    seller = models.ForeignKey(User,on_delete=models.CASCADE,related_name="listing_seller")
    created_at = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL,related_name="listing_winner")

    def __str__(self):
        return f'{self.title} - Posted by: {self.seller}'

#Class to store the bid details
class Bid(models.Model):
    bidder = models.ForeignKey(User,on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2,max_digits=10)
    listing = models.ForeignKey(AuctionListing,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.bidder} -  {self.amount} - {self.listing}'

#Class to store the comment details
class Comment(models.Model):
    commenter  = models.ForeignKey(User,on_delete=models.CASCADE)
    listing = models.ForeignKey(AuctionListing,on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.commenter} -  {self.listing.title} - {self.content}'

# Class to store the watchlist
class WatchList(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    listing = models.ManyToManyField(AuctionListing)

    def __str__(self):
       return f"{self.user}'s WatchList"