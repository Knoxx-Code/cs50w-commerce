from os import name
from django.urls import path

from . import views

app_name = 'auctions'

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create",views.create_listing, name="create_listing"),
    path("listings/<int:listing_id>",views.listing_view,name="listing_view"),
    path("listings/<int:listing_id>/close",views.close_listing,name="close_listing")
    
]
