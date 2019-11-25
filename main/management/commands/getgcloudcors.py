import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from google.cloud.storage import Client


class Command(BaseCommand):
    help = 'Get CORS Policy for Google Cloud Storage.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket', '-b',
            type=str,
            required=True,
            help='Bucket to manage. Required.',
        )

    def handle(self, *args, **options):
        client = Client(project=settings.GS_PROJECT_ID, credentials=settings.GS_CREDENTIALS)
        bucket = client.get_bucket(options['bucket'])

        terminal_size = shutil.get_terminal_size()
        print('-' * terminal_size.columns)
        print('Bucket name: {}'.format(options['bucket']))
        for i, policy in enumerate(bucket.cors):
            print('Policies[{}]: {}'.format(i, policy))
        print('-' * terminal_size.columns)
