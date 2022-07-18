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
python manage.py query --help
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
- query all objects
```shell
# query all books by default ordering
> python manage.py query myapp.Author
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
> python manage.py query myapp.Author --v
{"id": 1, "name": "R. F. Kuang", "age": 45}
{"id": 2, "name": "Raymond E. Feist", "age": 36}
{"id": 3, "name": "Tara McGowan-Ross", "age": 29}
---------------------
Count: 3
```

- query objects by ordering
```shell
> python manage.py query myapp.Author --order-by=-id
Author object (3)
Author object (2)
Author object (1)
---------------------
Count: 3
```
> Use comma to separate ordering fields if there are more than one field.

- query objects using filters
```shell
# Get author which ID is 1
> python manage.py query myapp.Author --filter id=1 --v
Author object (1)
---------------------
Count: 1
```

```shell
# query authors with specific IDs
> python manage.py query myapp.Author --filter id__in=1,3
Author object (1)
Author object (3)
---------------------
Count: 2
```

```shell
# query books which name contains "The" and price is lower than 15
> python manage.py query myapp.Book --filter name__contains=The,price__lt=15
Book object (1)
---------------------
Count: 1
```

```shell
# query books those published by a certain publisher
> python manage.py query myapp.Book --filter publisher__name__contains=Harper
Book object (1)
Book object (2)
---------------------
Count: 2
```

```shell
# query books those published by a certain publisher
> python manage.py query myapp.Book --filter author__name="R. F. Kuang"
Book object (1)
Book object (2)
---------------------
Count: 2
```

```shell
# query publishers which website is null
> python manage.py query myapp.Publisher --exclude website__isnull=True
Publisher object (1)
Publisher object (2)
---------------------
Count: 2
```

```shell
# query authors were created over a period of time.

> python manage.py query myapp.Book --filter created_at__range=2022-05-01T00:00:00,2022-05-31T23:59:59
Book object (1)
---------------------
Count: 1
```

> Note that DateTimeField supports ISO standard datetime or date format, e.g. <br>
>   2018-12-07T06:24:24.000000 <br>
    2018-12-07T06:24:24Z<br>
    2018-12-07 06:24:24<br>
    2018-12-07<br>

### Use in program 
- Query by filters in Django
```python
from queryset_cmd.backends import QuerySetFilter
from django.contrib.auth import get_user_model

User = get_user_model()

class SomeView:

    def get_queryset(self):
        queryset_filter = QuerySetFilter()
        queryset = queryset_filter.filter(User.objects.all(), **queryset_filter.query_params)
        return queryset

```
- Query by filters in Django Rest Framework
```python
from queryset_cmd.backends import QuerySetFilter
from django.contrib.auth import get_user_model

User = get_user_model()

class SomeView:
    filter_backends = [QuerySetFilter]
```