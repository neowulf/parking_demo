import logging

from django.test import TestCase
from django.urls import reverse

from parking.models import ParkingSpot

logger = logging.getLogger(__name__)


def create_parking_spots():
    ParkingSpot.objects.create(location=ParkingSpot.create_point(37.781533, -122.39661),
                               address='468 3rd St, San Francisco, CA 94107, USA')


class ParkingModelTests(TestCase):
    def test_empty_parking_spots(self):
        result = ParkingSpot.within_range(1, 1, 1)
        self.assertEqual(len(result), 0)

    def test_list_spots_within_radius(self):
        address = '468 3rd St, San Francisco, CA 94107, USA'

        lat = 37.781533
        lng = -122.39661
        radius = 10
        ParkingSpot.objects.create(location=ParkingSpot.create_point(lat, lng),
                                   address=address)
        result = ParkingSpot.within_range(lat, lng, radius)
        logger.debug(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].location.x, lng)
        self.assertEqual(result[0].location.y, lat)

    def test_list_spots_outside_radius(self):
        lat = 22
        lng = -22
        self.assertEqual(len(ParkingSpot.within_range(lat, lng, 10)), 0)


class ParkingIndexViewTests(TestCase):
    def request_available(self, lat, lng, radius):
        return self.client.get(reverse('parking:available'), {'lat': lat, 'lng': lng, 'radius': radius})

    def test_list_empty_parking_spots(self):
        response = self.request_available(1, 1, 1)
        self.assertEqual(response.status_code, 200)
        logger.debug(response)
        self.assertContains(response, """{"hits": {"from": 0, "page_size": 0, "total": 0}, "result": []}""")

    def test_list_parking_spots(self):

        create_parking_spots()

        lat = 37.781533
        lng = -122.39661
        radius = 10
        response = self.request_available(lat, lng, radius)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            """{"hits": {"from": 0, "page_size": 1, "total": 1}, "result": [{"id": 1, "lat": -122.39661, "lng": 37.781533, "address": "468 3rd St, San Francisco, CA 94107, USA"}]}""")





# class ReservationModelTests(TestCase):
#     def test_make_reservation(self):
#         pass
#
#     def test_make_invalid_reservation(self):
#         pass
#
#
# class ParkingIndexViewTests(TestCase):
#     def test_list_parking_available(self):
#         response = self.client.get(reverse('parking:available'), {'lat': 1, 'lng': 2, 'radius': 3})
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, """{"size": 0, "result": []}""")
#


"""

Requirements

    See available parking spots on a map
    Search for an address and find nearby parking
    Reserve a parking spot
    View existing reservations
    Cancel an existing reservation
    Show the user the cost of the reservation

Bonus
    Automated tests
    Require users to use phone numbers to sign up.
        Validate that the phone numbers are real.
    Additional features (whatever you think would be useful.)
    
Parking Spots
    1. List available spots at a given time
    2. Reserve a parking spot given a time slot, parking spot id, and user id
    3. View existing reservations given a user id
    4. Cancel existing reservation id given a reservation id and user id
    5. Show the user the cost of the reservation
    
"""
