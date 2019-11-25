import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from google.cloud.storage import Client


class Command(BaseCommand):
    help = 'Set CORS Policy for Google Cloud Storage.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket', '-b',
            type=str,
            required=True,
            help='Bucket to manage. Required.',
        )
        parser.add_argument(
            '--scheme', '-s'
            type=str,
            default='https',
            help='Specify scheme. Default is "https"',
        )
        parser.add_argument(
            '--host', '-H'
            type=str,
            default='booxmix.com',
            help='Host to allow CORS. Default is "booxmix.com"',
        )
        parser.add_argument(
            '--max_age_seconds', '-max', '-m',
            type=int,
            default=3600,
            help='Specify max age for preflight request. Default is 3600 seconds',
        )
        parser.add_argument(
            '--append',
            action='store_true',
            help='If you want to append new policy to list of existing ones, add this option. By default, old settings will be replaced and deleted by new one.',
        )

    def handle(self, *args, **options):
        origin = '{}://{}'.format(options['scheme'], options['host'])
        client = Client(project=settings.GS_PROJECT_ID, credentials=settings.GS_CREDENTIALS)
        bucket = client.get_bucket(options['bucket'])
        policies = bucket.cors
        new_policies = {
            'origin': [origin],
            'method': ['GET', 'HEAD'],
            'responseHeader': ['Content-Type'],
            'maxAgeSeconds': options['max_age_seconds'],
        }
        if options['append']:
            policies.append(new_policies)
        else:
            policies = [new_policies]
        bucket.cors = policies
        bucket.update()

        terminal_size = shutil.get_terminal_size()
        print('-' * terminal_size.columns)
        print('Bucket name: {}'.format(options['bucket']))
        for i, policy in enumerate(bucket.cors):
            print('Policies[{}]: {}'.format(i, policy))
        print('-' * terminal_size.columns)
        print('CORS Policy for {} are updated successfully.'.format(options['bucket']))
