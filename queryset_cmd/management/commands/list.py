from django.apps import apps
from django.forms import model_to_dict

from ..base import QuerySetCommand


class Command(QuerySetCommand):

    def add_arguments(self, parser):
        model_labels = ' | '.join(model._meta.label for model in apps.get_models())
        parser.add_argument(
            'model_class', type=apps.get_model,
            help='Model name with app label. Choice are: \n' + model_labels,
        )
        parser.add_argument(
            '--v', action='store_true', default=False
        )
        parser.add_argument(
            '--all', action='store_true', default=False
        )
        super().add_arguments(parser)

    def handle(self, *args, **options):
        limit = 20
        super().handle(*args, **options)
        model_class = options['model_class']
        self.stdout.write(self.style.MIGRATE_HEADING(f'Querying {model_class.__name__} ...'))
        objects = self.filter_queryset(
            model_class.objects.all(),
            order_by=options.get('order_by'),
            limit=options.get('limit'),
            strict=options.get('strict')
        )
        total_count = objects.count()
        brief_show = False
        if total_count > limit and not options.get('all'):
            brief_show = True
            objects = objects[:limit]

        for obj in objects:
            if options.get('v'):
                self.stdout.write(str(model_to_dict(obj)))
            else:
                self.stdout.write(f'{obj}')

        self.stdout.write('---------------------')
        self.stdout.write(f'Count: {total_count}')
        if brief_show:
            self.stdout.write(
                self.style.WARNING(
                    f'\nNOTICE: Only first {limit} objects were listed. '
                    '\n        Use --all to display all objects.')
            )
