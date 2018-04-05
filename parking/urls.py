
from django.urls import path

from . import views

app_name = 'parking'

urlpatterns = [
    # list parking spots given lat, lng, radius in meters
    path('v1/parking_spots/available', views.available, name='available'),

    # reserve parking spot given a time slot, parking spot id and user id
    # put with json request body
    path('v1/parking_spots/reserve', views.make_reservation, name='reserve'),

    # view existing reservations given a user id
    # cancel existing reservation given a user id and parking id
    # show the user the cost of the reservation

]