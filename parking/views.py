import json
import logging

from django.http import HttpResponse

from parking.models import ParkingSpot

logger = logging.getLogger(__name__)


# Create your views here.
def available(request):
    lat, lng, radius = float(request.GET['lat']), \
                       float(request.GET['lng']), \
                       float(request.GET['radius'])

    logger.debug('Getting the available parking spots at %s %s %s!' % (lat, lng, radius))

    # todo https://docs.djangoproject.com/en/2.0/ref/models/querysets/#when-querysets-are-evaluated
    query_result_set = ParkingSpot.within_range(lat, lng, radius)
    result_set = []
    for result in query_result_set:
        result_set.append({
            'id': result.id,
            'lat': result.location.x,
            'lng': result.location.y,
            'address': result.address
        })

    response = {
        'hits': {
            'from': 0,
            'page_size': len(result_set),
            'total': len(result_set)
        },
        'result': result_set
    }
    response = json.dumps(response)
    logger.info(response)
    return HttpResponse(response)
