import json
import logging

from django.test import TestCase
from django.urls import reverse

from parking.models import ParkingSpot, ParkingSpotReservation

logger = logging.getLogger(__name__)
from django.utils.dateparse import parse_datetime


def create_parking_spots_and_reservations():
    ParkingSpot.objects.create(location=ParkingSpot.create_point(37.781533, -122.39661),
                               address='468 3rd St, San Francisco, CA 94107, USA')
    ParkingSpot.objects.create(location=ParkingSpot.create_point(37.781345, -122.396861),
                               address='125a Stillman St, San Francisco, CA 94107, USA')
    ParkingSpot.objects.create(location=ParkingSpot.create_point(37.781055, -122.397206),
                               address='135 Stillman St, San Francisco, CA 94107, USA')
    ParkingSpot.objects.create(location=ParkingSpot.create_point(37.780604, -122.397851),
                               address='161-169 Stillman St, San Francisco, CA 94107, USA')
    ParkingSpot.objects.create(location=ParkingSpot.create_point(37.8079996, -122.4177434),
                               address='Fisherman\'s Wharf, San Francisco, CA, USA')
    ParkingSpotReservation.objects.create(user_id=1, parkingspot=ParkingSpot.objects.get(pk=1),
                                          start_ts=parse_datetime('2018-10-03T19:00:00Z'),
                                          end_ts=parse_datetime('2018-10-03T20:00:00Z'))


class ParkingModelTests(TestCase):
    def test_empty_parking_spots(self):
        result = ParkingSpot.within_range(1, 1, 1, 0, 10)
        self.assertEqual(len(result), 2)

    def test_list_spots_within_radius(self):
        address = '468 3rd St, San Francisco, CA 94107, USA'

        lat = 37.781533
        lng = -122.39661
        radius = 10
        ParkingSpot.objects.create(location=ParkingSpot.create_point(lat, lng),
                                   address=address)
        result = ParkingSpot.within_range(lat, lng, radius, 0, 10)
        logger.debug(result)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0].location.x, lng)
        self.assertEqual(result[1][0].location.y, lat)

    def test_list_spots_outside_radius(self):
        lat = 22
        lng = -22
        self.assertEqual(len(ParkingSpot.within_range(lat, lng, 10, 0, 10)[1]), 0)


class ParkingIndexViewTests(TestCase):
    def request_available(self, lat, lng, radius,
                          offset=0, page_size=10,
                          start_ts=None, end_ts=None):
        return self.client.get(reverse('parking:available'), {'lat': lat,
                                                              'lng': lng,
                                                              'radius': radius,
                                                              'offset': offset,
                                                              'page_size': page_size,
                                                              'start_ts': start_ts,
                                                              'end_ts': end_ts})

    def test_list_empty_parking_spots(self):
        response = self.request_available(1, 1, 1)
        self.assertEqual(response.status_code, 200)
        logger.debug(response)
        json_data = json.loads(response.content)
        self.assertEquals(json_data['hits']['offset'], 0)
        self.assertContains(response, """{"hits": {"offset": 0, "page_size": 0, "total": 0}, "result": []}""")

    def test_list_parking_spots_within_10_meters(self):
        create_parking_spots_and_reservations()

        lat = 37.781533
        lng = -122.39661
        radius = 10
        response = self.request_available(lat, lng, radius)
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertEquals(len(json_data['result']), 1)
        self.assertEquals(json_data['result'][0]['lat'], lat)
        self.assertEquals(json_data['result'][0]['lng'], lng)
        # self.assertContains(response,
        #                     """{"hits": {"from": 0, "page_size": 1, "total": 1}, "result": [{"id": 1, "lat": -122.39661, "lng": 37.781533, "address": "468 3rd St, San Francisco, CA 94107, USA"}]}""")

    def test_list_parking_spots_within_5000_meters(self):
        create_parking_spots_and_reservations()

        lat = 37.781533
        lng = -122.39661
        radius = 5000
        response = self.request_available(lat, lng, radius)
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertEquals(len(json_data['result']), 5)
        self.assertEquals(json_data['result'][0]['lat'], 37.781533)
        self.assertEquals(json_data['result'][1]['lat'], 37.781345)

    def test_list_parking_spots_reservation_agnostic(self):
        create_parking_spots_and_reservations()

        lat = 37.781533
        lng = -122.39661
        radius = 50
        response = self.request_available(lat, lng, radius)
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEquals(json_data['hits']['total'], 2)

    def test_list_parking_spots_overlap_starttime(self):
        create_parking_spots_and_reservations()

        response = self.request_available(lat=37.781533, lng=(-122.39661), radius=50,
                                          start_ts='2018-10-03T18:30:00Z',
                                          end_ts='2018-10-03T19:30:00Z')
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEquals(json_data['hits']['total'], 1)

    def test_list_parking_spots_overlap_endtime(self):
        create_parking_spots_and_reservations()

        response = self.request_available(lat=37.781533, lng=(-122.39661), radius=50,
                                          start_ts='2018-10-03T19:30:00Z',
                                          end_ts='2018-10-03T20:30:00Z')
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEquals(json_data['hits']['total'], 1)

    def test_list_parking_spots_overlap_midtime(self):
        create_parking_spots_and_reservations()

        response = self.request_available(lat=37.781533, lng=(-122.39661), radius=50,
                                          start_ts='2018-10-03T19:30:00Z',
                                          end_ts='2018-10-03T19:45:00Z')
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEquals(json_data['hits']['total'], 1)

    def test_list_parking_spots_eclipsing_existing(self):
        create_parking_spots_and_reservations()

        response = self.request_available(lat=37.781533, lng=(-122.39661), radius=50,
                                          start_ts='2018-10-03T15:30:00Z',
                                          end_ts='2018-10-03T22:45:00Z')
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEquals(json_data['hits']['total'], 1)

class ReservationViewTests(TestCase):
    def test_make_invalid_reservation(self):
        request_payload = {
            "user_id": 1,
            "parkingspot_id": 1,
            "start_ts": "2018-10-03T21:00:00Z",
            "end_ts": "2018-10-03T19:00:00Z"
        }
        response = self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        self.assertEqual(response.status_code, 404)

    def test_make_invalid_reservation_in_past(self):
        create_parking_spots_and_reservations()

        request_payload = {
            "user_id": 1,
            "parkingspot_id": 1,
            "start_ts": "2016-10-03T21:00:00Z",
            "end_ts": "2018-10-03T19:00:00Z"
        }
        response = self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        self.assertEqual(response.status_code, 400)

    def test_make_valid_reservation(self):
        create_parking_spots_and_reservations()

        request_payload = {
            "user_id": 1,
            "parkingspot_id": 1,
            "start_ts": "2018-10-03T22:00:00Z",
            "end_ts": "2018-10-03T23:00:00Z"
        }
        response = self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        logger.info(json.dumps(json_data))
        self.assertEquals(json_data['parkingspot']['address'], '468 3rd St, San Francisco, CA 94107, USA')
        # the following shows that an insert was made
        self.assertEquals(json_data['parkingspot_reservation']['id'], 2)
        self.assertEquals(json_data['parkingspot_reservation']['parkingspot'], 1)

    def test_make_invalid_duplicate_reservation(self):
        create_parking_spots_and_reservations()

        request_payload = {
            "user_id": 1,
            "parkingspot_id": 1,
            "start_ts": "2018-10-03T19:00:00Z",
            "end_ts": "2018-10-03T20:00:00Z"
        }
        self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        response = self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        logger.info('Response: %s' % response.content)
        self.assertEqual(response.status_code, 400)

    def test_make_invalid_reservation_overlapping_starttime(self):
        request_payload = {
            "user_id": 1,
            "parkingspot_id": 1,
            "start_ts": "2018-10-03T21:30:00Z",
            "end_ts": "2018-10-03T22:30:00Z"
        }
        response = self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        self.assertEqual(response.status_code, 404)

    def test_make_invalid_reservation_overlapping_endtime(self):
        request_payload = {
            "user_id": 1,
            "parkingspot_id": 1,
            "start_ts": "2018-10-03T22:30:00Z",
            "end_ts": "2018-10-03T23:30:00Z"
        }
        response = self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        self.assertEqual(response.status_code, 404)

    def test_make_invalid_reservation_overlapping_midtime(self):
        request_payload = {
            "user_id": 1,
            "parkingspot_id": 1,
            "start_ts": "2018-10-03T22:30:00Z",
            "end_ts": "2018-10-03T22:45:00Z"
        }
        response = self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        self.assertEqual(response.status_code, 404)

    def test_make_invalid_reservation_eclipsing_existing(self):
        request_payload = {
            "user_id": 1,
            "parkingspot_id": 1,
            "start_ts": "2018-10-03T20:00:00Z",
            "end_ts": "2018-10-03T23:45:00Z"
        }
        response = self.client.post(reverse('parking:reserve'), json.dumps(request_payload), 'json')
        self.assertEqual(response.status_code, 404)


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
    
    
"""
