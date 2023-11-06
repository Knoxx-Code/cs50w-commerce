from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render,redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import AuctionListing, User, Bid
from . import forms

def index(request):
    auction_listings = AuctionListing.objects.all().order_by('title')
    return render(request, "auctions/index.html",{
        'listings': auction_listings
    })


def login_view(request):
    
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            next_url = request.GET.get('next')
            
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")

@login_required(login_url='/auctions/login/')
def create_listing(request):

    if request.method == 'POST':
        listings_form = forms.CreateListing(request.POST)
        if listings_form.is_valid():
            new_listing = listings_form.save(commit=False)
            new_listing.seller = request.user
            new_listing.save()
            return redirect('auctions:index')
    else:
        listings_form = forms.CreateListing()
    
    return render(request,'auctions/create_listing.html',{
        'form': listings_form
    })


def listing_view(request,listing_id):
    listing = AuctionListing.objects.get(id=listing_id)
    no_of_bids = Bid.objects.filter(listing=listing).count()
    top_bids = Bid.objects.filter(listing=listing).order_by('-amount')[:3]
    bid_msg = None
    if request.method == 'POST':
        bid_form = forms.PlaceBid(request.POST)
        if bid_form.is_valid():
            new_bid = bid_form.save(commit=False)
            if new_bid.amount < listing.starting_bid:
                bid_form.add_error('amount','Bid amount must be greater than or equal to starting bid')
            else:
                #Get the bids made on the listing
                existing_bids = Bid.objects.filter(listing=listing)
                if existing_bids.exists():
                    highest_bid = existing_bids.order_by('-amount').first()
                    if new_bid.amount <= highest_bid.amount:
                         bid_form.add_error('amount','Bid amount must be greater than current highest bid')
                    else:
                        new_bid.bidder = request.user
                        new_bid.listing = listing
                        new_bid.save()
                else:
                    new_bid.bidder = request.user
                    new_bid.listing = listing
                    new_bid.save()
            # bid_msg = 'Bid placed successfully'
    else:
        bid_form = forms.PlaceBid()
            
        

    return render(request,'auctions/listing.html',{
        "listing": listing,
        "bids": no_of_bids,
        "bid_form": bid_form,
        "top_bids": top_bids
        # "bid_msg" : bid_msg
        
    })

