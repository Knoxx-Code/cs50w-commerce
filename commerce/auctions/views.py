


from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render,redirect
from django.urls import is_valid_path, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import AuctionListing, Category, User, Bid, WatchList,Comment
from . import forms



# Loads the index view which contains tne active listings
def index(request):
    auction_listings = AuctionListing.objects.all().order_by('title')
    return render(request, "auctions/index.html",{
        'listings': auction_listings
    })


# Handles login
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
            # If a user logs in while viewing a listing this redirects the user to the right listing
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


# Handles logout
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))

# Handles registration
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


# Handles the creation of a listing
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


# Handles all actions when viewing a particular listing
def listing_view(request,listing_id):
    
    listing = get_object_or_404(AuctionListing, id=listing_id)

    watchlist_listings = []

    # Check if a user is logged in and get all listings in a users watchlist
    if request.user.is_authenticated:
        try:
            watchlist = WatchList.objects.get(user=request.user)
            watchlist_listings = watchlist.listing.all()
        except WatchList.DoesNotExist:
            watchlist_listings = []
   
    
    no_of_bids = Bid.objects.filter(listing=listing).count()
    top_bids = Bid.objects.filter(listing=listing).order_by('-amount')[:3]
    winner = None

    

    # Check if a listing is closed and get the winner if bids were placed
    if listing.status == 'completed':
        if listing not in watchlist_listings:
            return redirect('auctions:index')
        existing_bids = Bid.objects.filter(listing=listing)
        highest_bid = existing_bids.order_by('-amount').first()
        winner = highest_bid.bidder
        bid_form = None
    else:
        if request.method == 'POST':
            # Handle the bidding process
            bid_form = forms.PlaceBid(request.POST)
            if bid_form.is_valid():
                new_bid = bid_form.save(commit=False)
                # Ensure that bid amount is greater than starting bid
                if new_bid.amount < listing.starting_bid:
                    messages.error(request,'Bid amount must be greater than or equal to starting bid')
                else:
                    # Get the bids made on the listing
                    existing_bids = Bid.objects.filter(listing=listing)
                    if existing_bids.exists():
                        highest_bid = existing_bids.order_by('-amount').first()
                        # Ensure bid is greater than highest bid
                        if new_bid.amount < highest_bid.amount:
                            messages.error(request,'Bid amount must be greater than current highest bid')
                        else:
                            new_bid.bidder = request.user
                            new_bid.listing = listing
                            new_bid.save()
                            messages.success(request,'Bid placed successfully')
                            
                            # If a user bids on a listing, it is automatically added to watchlist
                            if listing not in watchlist_listings:
                                watchlist.listing.add(listing)
                                return redirect('auctions:listing_view', listing_id=listing.id)
                            
                            return redirect('auctions:listing_view', listing_id=listing.id)
                    else:
                        new_bid.bidder = request.user
                        new_bid.listing = listing
                        new_bid.save()
                        messages.success(request,'Bid placed successfully')
                        
                        # If a user bids on a listing, it is automatically added to watchlist
                        if listing not in watchlist_listings:
                                watchlist.listing.add(listing)
                                return redirect('auctions:listing_view', listing_id=listing.id)
                        return redirect('auctions:listing_view', listing_id=listing.id)
        else:
            bid_form = forms.PlaceBid()
          
    # Comments creation
    if request.method == 'POST':
            
        comments_form = forms.MakeComment(request.POST)  

        if comments_form.is_valid():
            if request.user.is_authenticated:
                new_comment = comments_form.save(commit=False)
                new_comment.commenter = request.user
                new_comment.listing = listing
                new_comment.save()
                messages.success(request,'Your comment has been saved')
                return redirect('auctions:listing_view', listing_id=listing.id)
            else:
                messages.error(request,'You must be logged in to place a comment')
                return redirect('auctions:listing_view', listing_id=listing.id)
    else:
        comments_form = forms.MakeComment()  

    # Comments display
    comments = Comment.objects.filter(listing=listing)

    # Comments sorting
    sort_comment = request.GET.get('sort','oldest')

    if sort_comment == 'newest':
        comments = Comment.objects.filter(listing=listing).order_by('-timestamp')
    else:
        comments = Comment.objects.filter(listing=listing).order_by('timestamp')

    # Comments count
    comments_count = Comment.objects.filter(listing=listing).count()

    return render(request,'auctions/listing.html',{
        "listing": listing,
        "bids": no_of_bids,
        "bid_form": bid_form,
        "top_bids": top_bids,
        "watchlist_listings":watchlist_listings,
        "winner": winner,
        "comments_form": comments_form,
        "comments": comments,
        "comments_count": comments_count
        
    })

# Handles the closing of a listing
@login_required(login_url='/auctions/login/')
def close_listing(request,listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    existing_bids = Bid.objects.filter(listing=listing)
    #Checks if the current user is indeed the seller
    if listing.seller == request.user:
        # Check if there are existing bids on the listing
        if existing_bids.exists():
            listing.status = 'completed'
            winning_bid = existing_bids.order_by('-amount').first()
            listing.winner = winning_bid.bidder
        # If there are no existing bids disable the listing
        else:
            listing.status = 'disabled'
            listing.winner = None
    listing.save()

    return redirect('auctions:index')

# Handles the adding of a listing to a user's watchlist
@login_required(login_url='/auctions/login/')
def add_to_watchlist(request,listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    in_watchlist = WatchList.objects.filter(user=request.user,listing=listing)

    # Check if listing is in already in watchlist
    if in_watchlist.exists():
        messages.error(request,'This listing is already in your watchlist')
        return HttpResponseRedirect(reverse('auctions:index'))
    
    watchlist, created = WatchList.objects.get_or_create(user=request.user)
    watchlist.listing.add(listing)
    
    messages.success(request,'Listing successfully added to watchlist')

    return HttpResponseRedirect(reverse('auctions:listing_view',args=[listing_id]))
    
# Handles removal of a listing from the watchlist
@login_required(login_url='/auctions/login/')
def remove_from_watchlist(request,listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    watchlist = get_object_or_404(WatchList,user=request.user)

    watchlist.listing.remove(listing)
    messages.success(request,'Listing removed successfully from watchlist')
    
    return HttpResponseRedirect(reverse('auctions:listing_view',args=[listing_id]))

# Renders the watchlist page
@login_required(login_url='/auctions/login/')    
def load_watchlist(request):
    watchlist = get_object_or_404(WatchList,user=request.user)
    watchlist_listings = watchlist.listing.all()
    print(watchlist_listings)
    return render(request,"auctions/watchlist.html",{"watchlist_listings":watchlist_listings})

# Render the categories page
def display_categories(request):
    categories = Category.objects.all()
    return render(request,'auctions/categories.html',{
        "categories": categories
    })

# Show the listings in a category
def listings_in_category(request,category_name):
    category = get_object_or_404(Category,categoryName=category_name)

    listings = AuctionListing.objects.filter(category=category,status='active')

    return render(request,'auctions/listings_category.html',{
        "listings":listings,
        "category":category
    })

    