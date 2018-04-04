## Environment Setup

1. Setup conda environment using the `conda_environment.yml`
1. Update the spatialite library path in `parking_demo/settings.py`



## DB Setup

```bash
# To create migrations from the beginning
## rm -rf parking/migrations/ db.sqlite3

./manage.py migrate
./manage.py makemigrations parking
./manage.py migrate
```
