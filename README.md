# Environment Setup

1. Setup conda environment using the `conda_environment.yml`
1. Update the spatialite library path variable called `SPATIALITE_LIBRARY_PATH` in `parking_demo/settings.py`
1. Activate the conda environment before executing any of the following commands.

# DB Setup

```bash
./manage.py migrate
./manage.py shell < populate_db.py
```

# Run tests

```bash
DJANGO_LOG_LEVEL=INFO ./manage.py test parking
```

# Run server

```bash
./manage.py runserver
```

# Curl Commands

## Return parking spots given coordinates

| Query Parameters | Type | Description | Required | Default |
|---|---|---|---|
| lat  |  Float | Latitude  | yes |  |
| lng  |  Float | Longitude  |  yes  |  |
| radius  |  Float | Radius in meters  | yes  |  |
| offset  | Int  | Page start in the result set  | no  | 0 |
| page_size  | Int  |  Page size |  no  |  10 |
| start_ts  | Datetime  |  Available parking spot starting from | no  |  None  |
| end_ts  |  Datetime | Available parking spot ending at  | no  |  None |

1. `start_ts` and `end_ts` are optional but when applied, both parameters need to be provided.
    1. If these variables are missing, the result set will simply list the parking spots.
    1. If these variables are both provided, the result set will show the available parking spots which can be reserved.

### Sample Requests / Responses

```bash
curl -s "localhost:8000/parking/v1/parking_spots/available?lng=-122.39661&lat=37.781533&radius=100"

# Response

{
  "hits": {
    "offset": 0,
    "page_size": 3,
    "total": 3
  },
  "result": [
    {
      "id": 1,
      "lng": -122.39661,
      "lat": 37.781533,
      "address": "468 3rd St, San Francisco, CA 94107, USA"
    },
    {
      "id": 2,
      "lng": -122.396861,
      "lat": 37.781345,
      "address": "125a Stillman St, San Francisco, CA 94107, USA"
    },
    {
      "id": 3,
      "lng": -122.397206,
      "lat": 37.781055,
      "address": "135 Stillman St, San Francisco, CA 94107, USA"
    }
  ]
}
```

```
curl -s "localhost:8000/parking/v1/parking_spots/available?lng=-122.39661&lat=37.781533&radius=100&start_ts=2018-10-03T20%3A00%3A00Z&end_ts=2018-10-03T19%3A00%3A00Z"

# Response

{
  "hits": {
    "offset": 0,
    "page_size": 2,
    "total": 2
  },
  "result": [
    {
      "id": 2,
      "lng": -122.396861,
      "lat": 37.781345,
      "address": "125a Stillman St, San Francisco, CA 94107, USA"
    },
    {
      "id": 3,
      "lng": -122.397206,
      "lat": 37.781055,
      "address": "135 Stillman St, San Francisco, CA 94107, USA"
    }
  ]
}
```

## Reserve available parking spot

| Json Payload Parameters | Type | Description | Required  | Default |
|---|---|---|---|
| user_id  |  Int |  User's primary id | yes  |   |
| parkingspot_id  | Int  | Parking spot's id  |  yes  |  |
| start_ts  | Datetime  |  Available parking spot starting from | yes  |    |
| end_ts  |  Datetime | Available parking spot ending at  |  yes  |   |

1. The api will perform a final check before finalizing the reservation.
2. There could be a slight race condition between the check and the insert of the reservation record.

```bash
curl -XPOST -d '{
    "user_id": 1,
    "parkingspot_id": 1,
    "start_ts": "2018-10-03T19:00:00Z",
    "end_ts": "2018-10-03T20:00:00Z"
    }' "localhost:8000/parking/v1/parking_spots/reserve"
```
### Sample Requests / Responses

```bash
curl -XPOST -d '{
    "user_id": 1,
    "parkingspot_id": 1,
    "start_ts": "2018-10-03T19:00:00Z",
    "end_ts": "2018-10-03T20:00:00Z"
}' "localhost:8000/parking/v1/parking_spots/reserve"

{"exception": "Reservation not available."
```

```bash
curl -XPOST -d '{
    "user_id": 1,
    "parkingspot_id": 4,
    "start_ts": "2018-10-03T19:00:00Z",
    "end_ts": "2018-10-03T20:00:00Z"
}' "localhost:8000/parking/v1/parking_spots/reserve"

# Response

{
  "parkingspot": {
    "location": "SRID=4326;POINT (-122.397851 37.780604)",
    "address": "161-169 Stillman St, San Francisco, CA 94107, USA"
  },
  "parkingspot_reservation": {
    "id": 2,
    "user_id": 1,
    "parkingspot": 4,
    "start_ts": "2018-10-03T19:00:00Z",
    "end_ts": "2018-10-03T20:00:00Z"
  }
}
```