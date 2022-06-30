import json

from django.apps import apps
from django.forms import model_to_dict

from ..base import QuerySetCommand
from ..utils.json import JsonEncoder


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
        super().handle(*args, **options)
        model_class = options['model_class']

        all_objects = model_class.objects.all()
        limit = options.get('limit') or 20 if not options.get('all') else None

        objects = self.filter_queryset(
            all_objects,
            order_by=options.get('order_by'),
            limit=limit,
        )

        for obj in objects:
            if options.get('v'):
                self.stdout.write(json.dumps(obj, cls=JsonEncoder))
            else:
                self.stdout.write(f'{obj}')

        self.stdout.write('---------------------')
        self.stdout.write(f'Count: {objects.count()}')

        if limit and all_objects.count() > limit:
            # show briefly
            self.stdout.write(
                self.style.WARNING(
                    f'\nNOTICE: Only first {limit} objects were listed. '
                    '\n        Use --all to display all objects.')
            )
