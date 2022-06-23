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
        super().add_arguments(parser)

    def handle(self, *args, **options):
        super().handle(*args, **options)
        model_class = options['model_class']
        self.stdout.write(self.style.MIGRATE_HEADING(f'Querying {model_class.__name__} ...'))
        objects = self.filter_queryset(
            model_class.objects.all(),
            order_by=options.get('order_by'),
            limit=options.get('limit'),
            strict=options.get('strict')
        )
        count = objects.count()
        for obj in objects:
            if options.get('v'):
                self.stdout.write(str(model_to_dict(obj)))
            else:
                self.stdout.write(f'{obj}')

        self.stdout.write('---------------------')
        self.stdout.write('Object count: %s' % count)
