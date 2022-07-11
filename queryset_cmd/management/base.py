from django.core.management.base import BaseCommand

from queryset_cmd.management.utils.query import QuerySetFilter
from queryset_cmd.management.utils.text import query_str2dict


class QuerySetCommand(QuerySetFilter, BaseCommand):
    def add_arguments(self, parser):
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
            help='Queryset filter queries. see document for help.'
        )
        parser.add_argument(
            '--exclude', type=query_str2dict, default=None,
            help='Queryset exclude queries, similar to filter.'
        )

    def handle(self, *args, **options):
        if options.get('filter'):
            self.filter_kwargs.update(**options['filter'])
        if options.get('exclude'):
            self.exclude_kwargs.update(**options['exclude'])
