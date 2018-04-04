import logging

import json
from django.http import HttpResponse

logger = logging.getLogger(__name__)


# Create your views here.
def available(request):

    lat, lng, radius = float(request.GET['lat']), \
                       float(request.GET['lng']), \
                       float(request.GET['radius'])


    logger.debug('Getting the available parking spots at %s %s %s!' % (lat, lng, radius))
    result_set = []
    response = {
        'size': len(result_set),
        'result': result_set
    }
    return HttpResponse(json.dumps(response))
