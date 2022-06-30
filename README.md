# QuerySet Command
> Query database in terminal by ORM style. <br>
> Support common and related querying, except comprehensive querying (Q, F, aggregate, ...).

## Prerequisite
- Django 2.0 +

## Install
1. Put the app "queryset_cmd" directory into root of your project.
2. Add "queryset_cmd.apps.QuerysetCmd" to INSTALLED_APPS of settings.py.

## Usage
```shell
python manage.py list --help
```

## Examples
### Models
```python
# myapp/models.py
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=64)
    age = models.PositiveIntegerField()


class Publisher(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(max_length=255)
    website = models.CharField(max_length=128, null=True)


class Book(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()
    author = models.ManyToManyField(Author, related_name='books')
    publisher = models.ForeignKey(Publisher, models.CASCADE, related_name='books')
    created_at = models.DateTimeField(auto_now_add=True)
```
### Database Tables
- myapp_book

| id  | name                  | price  | publisher_id | created_at                 |
|:----|-----------------------|:------:|:------------:|----------------------------|
| 1   | The Poppy War         |   12   |      1       | 2022-05-23 16:00:00.354445 |
| 2   | The Queen of Storms   |  15.5  |      1       | 2022-06-30 05:59:33.321612 |
| 3   | Persephone's Children |  8.6   |      3       | 2022-06-30 05:59:33.321612 |

- myapp_publisher

| id  | name             | address           | website                             | 
|-----|------------------|-------------------|-------------------------------------|
| 1   | Harper Voyager   | New York City, US | https://www.harpervoyagerbooks.com/ |
| 2   | Dundurn Press    | Toronto, CA       | https://www.dundurn.com/            |
| 3   | Candlewick Press | Boston, US        | <null>                              |

- myapp_author

| id  | name              | age |
|-----|-------------------|:---:|
| 1   | R. F. Kuang       | 45  |
| 2   | Raymond E. Feist  | 36  |
| 3   | Tara McGowan-Ross | 29  |

- myapp_book_author

| id  | book_id  | author_id |
|-----|:--------:|:---------:|
| 1   |    1     |     1     |
| 2   |    2     |     2     |
| 3   |    2     |     3     |
| 4   |    3     |     3     |

### Commands
- List all objects
```shell
# List all books by default ordering
> python manage.py list myapp.Author
Author object (1)
Author object (2)
Author object (3)
---------------------
Count: 3
```
> Tips: <br>
> Use **--all** to see full output. By default, only first 20 objects will be displayed. <br>
> Use **--v** to see verbose output. <br>

```shell
> python manage.py list myapp.Author --v
{"id": 1, "name": "R. F. Kuang", "age": 45}
{"id": 2, "name": "Raymond E. Feist", "age": 36}
{"id": 3, "name": "Tara McGowan-Ross", "age": 29}
---------------------
Count: 3
```

- List objects by ordering
```shell
> python manage.py list myapp.Author --order-by=-id
Author object (3)
Author object (2)
Author object (1)
---------------------
Count: 3
```
> Use comma to separate ordering fields if there are more than one field.

- List objects using filters
```shell
# Get author which ID is 1
> python manage.py list myapp.Author --filter id=1 --v
Author object (1)
---------------------
Count: 1
```

```shell
# List authors with specific IDs
> python manage.py list myapp.Author --filter id__in=1,3
Author object (1)
Author object (3)
---------------------
Count: 2
```

```shell
# List books which name contains "The" and price is lower than 15
> python manage.py list myapp.Book --filter name__contains=The,price__lt=15
Book object (1)
---------------------
Count: 1
```

```shell
# List books those published by a certain publisher
> python manage.py list myapp.Book --filter publisher__name__contains=Harper
Book object (1)
Book object (2)
---------------------
Count: 2
```

```shell
# List books those published by a certain publisher
> python manage.py list myapp.Book --filter author__name="R. F. Kuang"
Book object (1)
Book object (2)
---------------------
Count: 2
```

```shell
# List publishers which website is null
> python manage.py list myapp.Publisher --exclude website__isnull=True
Publisher object (1)
Publisher object (2)
---------------------
Count: 2
```

```shell
# List authors were created over a period of time.
# Note that following commands are nearly same, separately using a datetime and date condition
> python manage.py list myapp.Book --filter created_at__range=2022-05-01T00:00:00,2022-05-31T23:59:59
> python namage.py list auth.User --filter last_login__range=2022-05-01,2022-06-01
Book object (1)
---------------------
Count: 1
```
