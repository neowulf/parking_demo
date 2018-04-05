import django
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import Distance
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, ForeignObject
from django.db.models.options import Options
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import ExtraWhere
from django.utils import timezone


class DbUtils():
    @staticmethod
    def join_to(table1, table2, field1, field2, queryset, alias=''):
        """
        table1 base

        Source: https://stackoverflow.com/a/37688104/1216965
        """

        # here you can set complex clause for join
        def extra_join_cond(where_class, alias, related_alias):
            if (alias, related_alias) == ('[sys].[columns]',
                                          '[sys].[database_permissions]'):
                where = '[sys].[columns].[column_id] = ' \
                        '[sys].[database_permissions].[minor_id]'
                children = [ExtraWhere([where], ())]
                wh = where_class(children)
                return wh
            return None

        dpj = ForeignObject(
            to=table2,
            on_delete=lambda: None,
            from_fields=[None],
            to_fields=[None],
            rel=None,
            related_name=None
        )
        dpj.opts = Options(table1._meta)
        dpj.opts.model = table1
        dpj.get_joining_columns = lambda: ((field1, field2),)
        dpj.get_extra_restriction = extra_join_cond

        dj = Join(
            table2._meta.db_table, table1._meta.db_table,
            'T', "LEFT JOIN", dpj, True)

        ac = queryset._clone()
        ac.query.join(dj)
        # hook for set alias
        alias and setattr(dj, 'table_alias', alias)
        return ac


class ParkingSpot(models.Model):
    location = PointField(help_text="geo coords of the parking spot")
    address = models.CharField(max_length=200)

    def __str__(self):
        return ('%s lat: %s lng: %s') % (self.id, self.location.x, self.location.y)

    @staticmethod
    def create_point(lat, lng):
        """
        "X and Y coordinates". X is longitude, Y is latitude.
        :param lat:
        :param lng:
        :return:
        """
        return fromstr("POINT(%s %s)" % (lng, lat))

    @staticmethod
    def within_range(lat, lng, radius_meters, offset, pagesize, start_ts=None, end_ts=None):
        ref_point = ParkingSpot.create_point(lat, lng)

        queryset = ParkingSpot.objects.filter(
            location__distance_lte=(ref_point, Distance(m=radius_meters))
        )

        if start_ts is not None and end_ts is not None:
            join_query = DbUtils.join_to(ParkingSpot, ParkingSpotReservation, 'id', 'id', queryset)
            queryset = join_query.filter(
                Q(parkingspotreservation__isnull=True) \
                | Q(parkingspotreservation__start_ts__gt=end_ts)
                | Q(parkingspotreservation__end_ts__lt=start_ts)
            )

        return queryset.count(), queryset[offset:pagesize]


class ParkingSpotReservation(models.Model):
    user_id = models.IntegerField()
    parkingspot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, blank=True, null=True)
    start_ts = models.DateTimeField('reservation start date')
    end_ts = models.DateTimeField('reservation end date')
    create_date = models.DateTimeField('creation date', auto_now_add=True, blank=True)

    def save(self, *args, **kwargs):
        if self.end_ts <= self.start_ts:
            raise ValidationError("End timestamp can't before start timestamp.")
        elif self.start_ts < django.utils.timezone.now():
            raise ValidationError("Start timestamp can't be in the past.")
        elif self.overlapping_reservations_exist(self.parkingspot, self.start_ts, self.end_ts) is not None:
            raise ValidationError("Reservation not available.")
        else:
            super().save(*args, **kwargs)

    @staticmethod
    def overlapping_reservations_exist(parkingspot, start, end):
        """
           ---|----|---
        1.  ^   ^
        2.      ^    ^
        3.  ^        ^
        4.      ^^
        5. ^^
        6.           ^^

        :param parkingspot:
        :param start:
        :param end:
        :return:
        """
        # TODO fix race conditions - stored procedure? Perform a shopping cart like transaction?
        # TODO cache query set results
        try:
            result = ParkingSpotReservation.objects.filter(

                Q(parkingspot__exact=parkingspot),

                # does the reservation overlap with any existing reservations?
                # 1 | 2 would catch 4
                # The following is 1 | 2 | 3
                (Q(start_ts__lte=end) & Q(end_ts__gte=end)) \
                | (Q(start_ts__lte=start) & Q(end_ts__gte=start)) \
                | (Q(start_ts__gte=start) & Q(end_ts__lte=end))
            )[0:1].get()
        except:
            result = None

        return result
