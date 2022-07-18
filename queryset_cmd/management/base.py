from django.core.management.base import BaseCommand

from queryset_cmd.backends import QuerySetFilter
from queryset_cmd.utils.text import query_str2dict


class QuerySetCommand(BaseCommand):
    filter_backend = QuerySetFilter(strict=True)

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
            self.filter_backend.filter_kwargs.update(**options['filter'])
        if options.get('exclude'):
            self.filter_backend.exclude_kwargs.update(**options['exclude'])
