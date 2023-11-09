
from email import message
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render,redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import AuctionListing, Category, User, Bid, WatchList
from . import forms

import time


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
    
    listing = get_object_or_404(AuctionListing, id=listing_id)
    try:
        watchlist = WatchList.objects.get(user=request.user)
        watchlist_listings = watchlist.listing.all()
    except WatchList.DoesNotExist:
        watchlist_listings = []
    
    no_of_bids = Bid.objects.filter(listing=listing).count()
    top_bids = Bid.objects.filter(listing=listing).order_by('-amount')[:3]
    winner = None

    if listing.status == 'completed':
        if listing not in watchlist_listings:
            return redirect('auctions:index')
        existing_bids = Bid.objects.filter(listing=listing)
        highest_bid = existing_bids.order_by('-amount').first()
        winner = highest_bid.bidder
        bid_form = None
    else:
        if request.method == 'POST':
            bid_form = forms.PlaceBid(request.POST)
            if bid_form.is_valid():
                new_bid = bid_form.save(commit=False)
                if new_bid.amount < listing.starting_bid:
                    messages.error(request,'Bid amount must be greater than or equal to starting bid')
                else:
                    #Get the bids made on the listing
                    existing_bids = Bid.objects.filter(listing=listing)
                    if existing_bids.exists():
                        highest_bid = existing_bids.order_by('-amount').first()
                        if new_bid.amount <= highest_bid.amount:
                            messages.error(request,'Bid amount must be greater than current highest bid')
                        else:
                            new_bid.bidder = request.user
                            new_bid.listing = listing
                            new_bid.save()
                            messages.success(request,'Bid placed successfully')
                            if listing not in watchlist_listings:
                                watchlist.listing.add(listing)
                                return redirect(request.META['HTTP_REFERER'])
                    else:
                        new_bid.bidder = request.user
                        new_bid.listing = listing
                        new_bid.save()
                        messages.success(request,'Bid placed successfully')
                        if listing not in watchlist_listings:
                                watchlist.listing.add(listing)
                                return redirect(request.META['HTTP_REFERER'])
        else:
            bid_form = forms.PlaceBid()
          
        

    return render(request,'auctions/listing.html',{
        "listing": listing,
        "bids": no_of_bids,
        "bid_form": bid_form,
        "top_bids": top_bids,
        "watchlist_listings":watchlist_listings,
        "winner": winner
        
    })

@login_required(login_url='/auctions/login/')
def close_listing(request,listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    existing_bids = Bid.objects.filter(listing=listing)
    if listing.seller == request.user:
        if existing_bids.exists():
            listing.status = 'completed'
            winning_bid = existing_bids.order_by('-amount').first()
            listing.winner = winning_bid.bidder
        else:
            listing.status = 'disabled'
            listing.winner = None
    listing.save()


    return redirect('auctions:index')

@login_required(login_url='/auctions/login/')
def add_to_watchlist(request,listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    in_watchlist = WatchList.objects.filter(user=request.user,listing=listing)

    if in_watchlist.exists():
        messages.error(request,'This listing is already in your watchlist')
        return HttpResponseRedirect(reverse('auctions:index'))
    
    watchlist, created = WatchList.objects.get_or_create(user=request.user)
    watchlist.listing.add(listing)
    
    messages.success(request,'Listing successfully added to watchlist')

    return HttpResponseRedirect(reverse('auctions:listing_view',args=[listing_id]))
    

@login_required(login_url='/auctions/login/')
def remove_from_watchlist(request,listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    watchlist = get_object_or_404(WatchList,user=request.user)

    watchlist.listing.remove(listing)
    messages.success(request,'Listing removed successfully from watchlist')
    
    return HttpResponseRedirect(reverse('auctions:listing_view',args=[listing_id]))

@login_required(login_url='/auctions/login/')    
def load_watchlist(request):
    watchlist = get_object_or_404(WatchList,user=request.user)
    watchlist_listings = watchlist.listing.all()
    print(watchlist_listings)
    return render(request,"auctions/watchlist.html",{"watchlist_listings":watchlist_listings})

def display_categories(request):
    categories = Category.objects.all()
    return render(request,'auctions/categories.html',{
        "categories": categories
    })

def listings_in_category(request,category_name):
    category = get_object_or_404(Category,categoryName=category_name)

    listings = AuctionListing.objects.filter(category=category,status='active')

    return render(request,'auctions/listings_category.html',{
        "listings":listings,
        "category":category
    })

    