import datetime
import warnings

from django.core.management.base import BaseCommand, CommandError
from django.db import models

from .utils import text
from .utils.datetime import to_aware_datetime
from .utils.text import query_str2dict


class QuerySetCommand(BaseCommand):
    class FilterFormat(object):

        exc = 'exclude__'

        def __init__(self, field_name):
            self.field_name = field_name
            self.isin = 'in'
            self.range = 'range'
            self.exact = 'exact'
            self.iexact = 'iexact'
            self.isnull = 'isnull'
            self.contains = 'contains'
            self.icontains = 'icontains'
            self.gt = 'gt'
            self.gte = 'gte'
            self.lt = 'lt'
            self.lte = 'lte'

        @property
        def filter_names(self):
            return (
                self.isin, self.range, self.exact, self.iexact, self.isnull, self.contains,
                self.icontains, self.gt, self.gte, self.lt, self.lte
            )

        def __getattr__(self, item):
            items = item.split('_')
            if item.startswith('_') and len(items) == 2:
                name = self.__getattribute__(''.join(items[1:]))
                return f'{self.field_name}__{name}'
            return super().__getattribute__(item)

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
            if text.is_list(value):
                value = text.str2iter(value)
            else:
                value = text.comma_separated_str2list(value)
        try:
            if isinstance(field, models.DateTimeField) or isinstance(refer_value, datetime.datetime):
                if iterable:
                    value = list(map(lambda x: to_aware_datetime(x), value))
                else:
                    value = to_aware_datetime(value)
            elif isinstance(field, models.BooleanField) or isinstance(refer_value, bool):
                if iterable:
                    # bool filed not support iterable value
                    raise ValueError(value)
                value = text.str2bool(value)
            elif isinstance(field, models.IntegerField) or isinstance(refer_value, int):
                if iterable:
                    value = list(map(lambda x: int(x), value))
                else:
                    value = text.str2int(value)
            elif isinstance(field, models.FloatField) or isinstance(refer_value, float):
                if iterable:
                    value = list(map(lambda x: float(x), value))
                else:
                    value = text.str2float(value)
            else:
                # str, bson ...
                pass

        except Exception as e:
            raise CommandError(e)

        return value

    def filter_queryset(self, queryset, order_by: list = None, limit: int = None, strict=False):
        """
        Filter queryset by layer, then by filter parameters and
        order queryset if necessary
        """
        # filtering except in case of passing parameter all=true
        if queryset:
            fields = queryset[0]._meta.concrete_fields

            def setup_query(kwargs: dict) -> dict:
                queries = dict()
                for fnc, fv in kwargs.items():
                    try:
                        fn, fc = fnc.split('__')
                    except ValueError:
                        fn = fnc
                        fc = 'exact'

                    ff = self.FilterFormat(fn)

                    hit_field = False
                    for i, field in enumerate(fields):
                        if fn == field.attname:
                            hit_field = True
                            if fc == ff.range:
                                fv = self._clean_query_value(fv, field, iterable=True)
                                if len(fv) != 2:
                                    raise CommandError('Condition range requires exactly two values.')
                                queries[ff._range] = fv
                            elif fc == ff.isnull:
                                try:
                                    fv = text.str2bool(fv)
                                except (TypeError, ValueError):
                                    raise CommandError('Condition isnull accepts only bool type.')
                                queries[ff._isnull] = fv
                            elif fc == ff.isin:
                                queries[ff._isin] = self._clean_query_value(fv, field, iterable=True)
                            else:
                                common_cond = (
                                    ff.exact, ff.iexact, ff.contains, ff.icontains,
                                    ff.gt, ff.gte, ff.lt, ff.lte)
                                cond_hit = False
                                for item in common_cond:
                                    if fc == item:
                                        queries[getattr(ff, f'_{item}')] = self._clean_query_value(fv, field)
                                        cond_hit = True
                                        break
                                if not cond_hit:
                                    cond_message = 'Not supported query with condition "%s".' % fc
                                    if strict:
                                        raise CommandError(cond_message)
                                    else:
                                        warnings.warn(cond_message)
                    if not hit_field:
                        field_message = f'Querying field "{fn}" is not a valid field.'
                        if strict:
                            raise CommandError(field_message)
                        else:
                            warnings.warn(field_message)

                return queries

            filter_conditions = setup_query(self.filter_kwargs)
            exclude_conditions = setup_query(self.exclude_kwargs)

            # print(filter_conditions, exclude_conditions)
            queryset = queryset.exclude(**exclude_conditions).filter(**filter_conditions)

            if order_by:
                try:
                    order_by = text.str2iter(order_by)
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
