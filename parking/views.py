import json
import logging

from django.core import serializers
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.http import JsonResponse, Http404
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from parking.models import ParkingSpot, ParkingSpotReservation

logger = logging.getLogger(__name__)


def available(request):
    if request.method != 'GET':
        raise Http404()

    lat, lng, radius, offset, pagesize, start_ts, end_ts = float(request.GET['lat']), \
                                                           float(request.GET['lng']), \
                                                           float(request.GET['radius']), \
                                                           int(request.GET.get('offset', 0)), \
                                                           int(request.GET.get('pagesize', 10)), \
                                                           request.GET.get('start_ts', None), \
                                                           request.GET.get('end_ts', None)

    if start_ts is not None and end_ts is not None:
        start_ts = parse_datetime(start_ts)
        end_ts = parse_datetime(end_ts)

    logger.debug('Getting the available parking spots at %s %s %s between %s and %s!' % (
        lat, lng, radius, start_ts, end_ts))

    total, query_result_set = ParkingSpot.within_range(lat, lng, radius, offset, pagesize, start_ts, end_ts)
    result_set = []
    for result in query_result_set:
        result_set.append({
            'id': result.id,
            'lng': result.location.x,
            'lat': result.location.y,
            'address': result.address
        })

    response = {
        'hits': {
            'offset': 0,
            'page_size': len(result_set),
            'total': total
        },
        'result': result_set
    }
    logger.info(response)
    return JsonResponse(response)


@csrf_exempt
def make_reservation(request):
    if request.method != 'POST':
        raise Http404()

    try:
        body_unicode = request.body.decode('utf-8')
        logger.info(body_unicode)
        body = json.loads(body_unicode)

        user_id = body['user_id']
        parkingspot_id = body['parkingspot_id']
        start = parse_datetime(body['start_ts'])
        end = parse_datetime(body['end_ts'])

        logger.info('incoming parameters %s' % body)

        logger.debug('Comparing start "%s" end "%s"' % (start, end))

        parkingspot_reservation = ParkingSpotReservation(user_id=user_id,
                                                         parkingspot=(ParkingSpot.objects.get(pk=parkingspot_id)),
                                                         start_ts=start,
                                                         end_ts=end)

        parkingspot_reservation.save()

        return JsonResponse({
            # TODO change this to provide the proper lat, long json data structure
            # POINT is not JSON serializable when model_to_dict is used
            'parkingspot': json.loads(serializers.serialize('json', [
                (ParkingSpot.objects.get(pk=parkingspot_id)), ]))[0]['fields'],
            'parkingspot_reservation': model_to_dict(parkingspot_reservation),
        })
    except ValidationError as validationerr:
        return JsonResponse({
            'exception': validationerr.message
        }, status=400)
    except ParkingSpotReservation.DoesNotExist:
        return JsonResponse({
            'exception': 'Reservation not available.'
        }, status=404)
    except ParkingSpot.DoesNotExist:
        return JsonResponse({
            'exception': 'Parking spot not available.'
        }, status=404)
    except Exception as exc:
        return JsonResponse({
            'exception': exc.message
        }, status=400)
