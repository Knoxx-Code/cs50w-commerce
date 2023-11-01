from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render,redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import AuctionListing, User
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
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


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
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required(login_url='/auctions/login')
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