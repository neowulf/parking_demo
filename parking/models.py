from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import Distance
from django.db import models


class ParkingSpot(models.Model):
    location = PointField(help_text="geo coords of the parking spot")
    address = models.CharField(max_length=200)

    def __str__(self):
        return ('%s lat: %s lng: %s') % (self.id, self.location.x, self.location.y)

    @staticmethod
    def create_point(lat, lng):
        return fromstr("POINT(%s %s)" % (lng, lat))

    @staticmethod
    def within_range(lat, lng, radius_meters):
        ref_point = ParkingSpot.create_point(lat, lng)
        return ParkingSpot.objects.filter(
            location__distance_lte=(ref_point, Distance(m=radius_meters)))
            # todo add distance from the ref_point
            # .distance(ref_point).order_by('distance')

