import copy
import datetime

from django.core.exceptions import FieldError
from django.core.management.base import BaseCommand, CommandError
from django.db import models

from .utils.datetime import to_aware_datetime
from .utils.text import (
    comma_separated_str2list,
    str2iter, is_list, str2bool, str2int, str2float,
    query_str2dict
)


class QuerySetCommand(BaseCommand):
    class FilterFormat(object):
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
            isin, range, exact, iexact, isnull,
            contains, icontains, gt, gte, lt, lte
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

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.filter_kwargs = dict()
        self.exclude_kwargs = dict()

    @staticmethod
    def _clean_query_value(value, field=None, refer_value=None,
                           iterable=False):
        """
        value_type is used for MongoDB data
        """
        if value == 'null':
            return None
        if iterable:
            # 转为可迭代对象
            if is_list(value):
                value = str2iter(value)
            else:
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
            pass

        return value

    def _setup_query(self, queryset, kwargs: dict) -> dict:
        assert queryset
        instance = queryset[0]
        queries = dict()

        for fnc, fv in kwargs.items():
            # makeup the field name and condition
            *fns, fc = fnc.split('__')
            if not fc:
                # e.g. name, mobile_phone, user(FK)
                fc = 'exact'
            else:
                if fc not in self.FilterFormat.builtin_conditions:
                    # e.g. user__username, user__id
                    fns.append(fc)
                    fc = 'exact'

            def _get_last_field(_meta=None, _fns=None):
                # find last field according to field name list
                if not _fns:
                    _fns = copy.copy(fns)
                if not _meta:
                    _meta = instance._meta

                _fns.reverse()
                _fn = _fns[-1]
                _fns.pop()

                _field = _meta.get_field(_fn)

                if hasattr(_field, '_meta'):
                    return _get_last_field(_field._meta, _fns)

                return _field

            last_field = _get_last_field()
            fields = last_field.related_model._meta.concrete_fields

            ffn = '__'.join(fns)  # full field name
            fn = fns[-1]  # field name
            ff = self.FilterFormat(ffn)

            for i, field in enumerate(fields):
                if fn in (field.attname, field.name):
                    hit_field = True
                    if fc == ff.range:
                        fv = self._clean_query_value(fv, field, iterable=True)
                        if len(fv) != 2:
                            raise CommandError('Condition range requires exactly two values.')
                    elif fc == ff.isnull:
                        try:
                            fv = str2bool(fv)
                        except (TypeError, ValueError):
                            raise CommandError('Condition isnull accepts only bool type.')
                    elif fc == ff.isin:
                        fv = self._clean_query_value(fv, field, iterable=True)
                    else:
                        common_cond = (
                            ff.exact, ff.iexact, ff.contains, ff.icontains,
                            ff.gt, ff.gte, ff.lt, ff.lte)
                        cond_hit = False
                        for item in common_cond:
                            if fc == item:
                                fv = self._clean_query_value(fv, field)
                                cond_hit = True
                                break
                        if not cond_hit:
                            hit_field = False

                        if hit_field:
                            break

            queries[ff.setup(fc)] = fv

        return queries

    def filter_queryset(self, queryset, order_by: list = None, limit: int = None, strict=False):
        """
        Filter queryset by layer, then by filter parameters and
        order queryset if necessary
        """
        # filtering except in case of passing parameter all=true
        if queryset:
            try:
                queryset = queryset.exclude(
                    **self._setup_query(queryset, self.exclude_kwargs)).filter(
                    **self._setup_query(queryset, self.filter_kwargs))
            except FieldError as e:
                raise CommandError(e)

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

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict', action='store_true', default=False
        )
        parser.add_argument(
            '--order-by', type=str, default=None,
            help='Queryset order argument'
        )
        parser.add_argument(
            '--limit', type=int, default=None,
            help='Queryset sliced by, a positive integer requires.'
        )
        parser.add_argument(
            '--filter', type=query_str2dict, default=None,
            help='Queryset filter queries. e.g. name__contains=Robert,birthday__range=1980-01-01,1980-12-31'
        )
        parser.add_argument(
            '--exclude', type=query_str2dict, default=None,
            help='Queryset exclude queries, is similar to filter.'
        )

    def handle(self, *args, **options):
        if options.get('filter'):
            self.filter_kwargs.update(**options['filter'])
        if options.get('exclude'):
            self.exclude_kwargs.update(**options['exclude'])
