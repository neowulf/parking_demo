from django.test import TestCase
from django.urls import reverse


class ParkingIndexViewTests(TestCase):
    def test_list_parking_available(self):
        response = self.client.get(reverse('parking:available'), {'lat': 1, 'lng': 2, 'radius': 3})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """{"size": 0, "result": []}""")


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
