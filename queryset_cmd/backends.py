import copy
import datetime
import typing

from django.core.exceptions import FieldError, FieldDoesNotExist
from django.db import models
from django.db.models.base import ModelBase

from utils.datetime import to_aware_datetime
from utils.text import (
    comma_separated_str2list,
    str2iter, is_list, str2bool, str2int, str2float
)

__all__ = [
    'QuerySetFilter',
    'QueryError'
]


class QueryError(Exception):
    pass


class QuerySetFilter(object):
    strict = False

    def __new__(cls, *args, **kwargs):
        cls.filter_kwargs = dict()
        cls.exclude_kwargs = dict()
        return super().__new__(cls)

    def __init__(self, **kwargs):
        if 'strict' in kwargs and isinstance(kwargs['strict'], bool):
            self.strict = kwargs['strict']
        self._view = None
        self._request = None
        super().__init__()

    class FilterFormat:
        isin = 'in'
        range = 'range'
        exact = 'exact'
        iexact = 'iexact'
        isnull = 'isnull'
        contains = 'contains'
        icontains = 'icontains'
        gt = 'gt'
        gte = 'gte'
        lt = 'lt'
        lte = 'lte'

        builtin_conditions = (
            exact, iexact, isnull,
            contains, icontains, gt, gte, lt, lte,
            isin, range
        )

        exc = 'exclude__'

        def __init__(self, field_name):
            self.field_name = field_name

        def setup(self, fc):
            """
            Setup final condition clauses
            """
            return '__'.join([self.field_name, fc])

        def exclude(self, cond):
            return self.exc + cond

    @staticmethod
    def _clean_query_value(value, field=None, refer_value=None,
                           iterable=False):
        """
        value_type is used for MongoDB data
        """
        if value == 'null':
            return None
        if iterable:
            if is_list(value):
                # '["a", "b", "c"]'
                value = str2iter(value)
            else:
                # 'a,b,c'
                value = comma_separated_str2list(value)

        if isinstance(field, models.DateTimeField) or isinstance(refer_value, datetime.datetime):
            if iterable:
                value = list(map(lambda x: to_aware_datetime(x), value))
            else:
                value = to_aware_datetime(value)
        elif isinstance(field, models.BooleanField) or isinstance(refer_value, bool):
            if iterable:
                # bool filed not support iterable value
                raise ValueError(value)
            value = str2bool(value)
        elif isinstance(field, models.IntegerField) or isinstance(refer_value, int):
            if iterable:
                value = list(map(lambda x: int(x), value))
            else:
                value = str2int(value)
        elif isinstance(field, models.FloatField) or isinstance(refer_value, float):
            if iterable:
                value = list(map(lambda x: float(x), value))
            else:
                value = str2float(value)
        else:
            # str, bson ...
            # if re.match('".*"', value):
            #     value = value.strip('"')
            # elif re.match("'.*'", value):
            #     value = value.strip("'")
            pass

        return value

    def _setup_query(self, meta, kwargs: dict) -> dict:
        queries = dict()
        builtin_conditions = self.FilterFormat.builtin_conditions

        for fnc, fv in kwargs.items():
            # makeup the field name and condition
            *fns, fc = fnc.split('__')
            if not fc:
                # e.g. name, mobile_phone, user(FK)
                fc = 'exact'
            else:
                if fc not in builtin_conditions:
                    # e.g. user__username, user__id
                    fns.append(fc)
                    fc = 'exact'

            def _get_last_field(_meta=None, _fns=None):
                # find last field according to field name list
                if not _fns:
                    _fns = copy.copy(fns)
                if not _meta:
                    _meta = meta

                _fn = _fns.pop(0)
                try:
                    _field = _meta.get_field(_fn)
                except FieldDoesNotExist as e:
                    if self.strict:
                        raise QueryError(e)
                    else:
                        return
                related_model = _field.related_model
                if hasattr(related_model, '_meta') and _fns:
                    return _get_last_field(getattr(related_model, '_meta'), _fns)

                return _field

            ffn = '__'.join(fns)  # full field name
            fn = fns[-1]  # field name
            ff = self.FilterFormat(ffn)

            field = _get_last_field()
            if not field:
                if not self.strict:
                    continue
                else:
                    raise QueryError('Invalid field name {0}'.format(fn))

            if fn in (field.attname, field.name):
                hit_field = False
                if fc == ff.range:
                    fv = self._clean_query_value(fv, field, iterable=True)
                    if len(fv) != 2:
                        raise QueryError('Condition range requires exactly two values.')
                    hit_field = True
                elif fc == ff.isnull:
                    try:
                        fv = str2bool(fv)
                    except (TypeError, ValueError):
                        raise QueryError('Condition isnull accepts only bool type.')
                    hit_field = True
                elif fc == ff.isin:
                    fv = self._clean_query_value(fv, field, iterable=True)
                    hit_field = True
                else:
                    for item in builtin_conditions:
                        if fc == item:
                            fv = self._clean_query_value(fv, field)
                            hit_field = True
                            break
                if hit_field:
                    queries[ff.setup(fc)] = fv

        return queries

    @property
    def query_params(self):
        exclude_fields = getattr(self._view, 'exclude_fields', dict())
        params = dict()
        for k, v in self._request.query_params.items():
            if v and k not in exclude_fields:
                params[k] = v
        return params

    def filter_queryset(self, request, queryset, view):
        self._view = view
        self._request = request
        return self.filter(queryset, **self.query_params)

    def filter(self, queryset, order_by: typing.Union[tuple, list] = None, limit: int = None,
               filter_kwargs: dict = None, exclude_kwargs: dict = None, **kwargs):
        """
        Filter queryset by layer, then by filter parameters and
        order queryset if necessary
        filter_kwargs: {"id": 1}
        exclude_kwargs: {"id": 1}
        kwargs: {"exclude__id": 1} (same to exclude_kwargs {"id": 1}) or {"id": 1} (same to filter_kwargs)
        """
        # filtering except in case of passing parameter all=true
        filter_kwargs = filter_kwargs or self.filter_kwargs
        exclude_kwargs = exclude_kwargs or self.exclude_kwargs

        # setup uncertain query params
        for k, v in kwargs.items():
            if k.startswith(self.FilterFormat.exc):
                exclude_kwargs.update({k.replace(self.FilterFormat.exc, ''): v})
            else:
                filter_kwargs.update({k: v})

        if isinstance(queryset, ModelBase):
            queryset = getattr(queryset, '_meta').default_manager.all()

        meta = getattr(queryset.model, '_meta')

        try:
            queryset = queryset.exclude(
                **self._setup_query(meta, exclude_kwargs)).filter(
                **self._setup_query(meta, filter_kwargs))
        except FieldError as e:
            raise QueryError(e)

        if order_by:
            try:
                order_by = str2iter(order_by)
            except TypeError:
                pass
            if isinstance(order_by, str):
                order_by = (order_by,)

            queryset = queryset.order_by(*order_by)

        if limit:
            assert isinstance(limit, int)
            queryset = queryset[:limit]

        return queryset
