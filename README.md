# QuerySet Command
> Query database in terminal with ORM style. <br>
> Support common querying, except comprehensive querying (Q, F, aggregate, ...).

## Prerequisite
- Django 2.0 +

## Install
1. Put app "queryset_cmd" to root of your project.
2. Add "queryset_cmd.apps.QuerysetCmd" to your settings.py.

## Usage
```shell
python manage.py list --help
```

## Examples
```shell
# List all users by default ordering
python manage.py auth.User

# List users whose name contains "Bird" and their ID are bigger than 10
python manage.py auth.User --filter name__contains=Bird,id__gt=10

# List users never logged in and their ID less than or equal 100
python manage.py auth.User --exclude last_login__isnull=True --filter id__lte=100

# List users with specific IDs
python manage.py auth.User --filter id=1
python manage.py auth.User --filter id__in=1,3,5

# List users registered over a period of time.
# Note that following commands are nearly same, separately using a datetime and date condition
python manage.py auth.User --filter last_login__range=2022-05-01T00:00:00,2022-05-31T23:59:59
python namage.py auth.User --filter last_login__range=2022-05-01,2022-06-01
```
