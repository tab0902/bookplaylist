import json
import requests
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from bookplaylist.utils import APIMixin
from main.models import (
    Book, Playlist, Provider,
)


class Command(APIMixin, BaseCommand):
    help = 'Get book data from API and update the records in DB.'

    def add_arguments(self, parser):
        default_provider = self.provider
        parser.add_argument(
            '--provider', '-p',
            type=str,
            choices=[p[0] for p in Provider.objects.values_list('slug')],
            nargs='?',
            default=default_provider.slug,
            help='Specify the provider of book data. Default is {}'.format(default_provider.slug),
        )

    def handle(self, *args, **options):
        provider = Provider.objects.get(slug=options['provider'])
        endpoint = provider.endpoint
        isbn_list = [p[0] for p in Playlist.all_objects.all().values_list('book')]
        for isbn in isbn_list:
            params = {
                'applicationId': settings.RAKUTEN_APPLICATION_ID,
                'isbn': isbn,
            }

            response = self.get_book_data(params)
            if response.status_code == requests.codes.bad_request:
                print('No data found.')
            elif 'error' in response:
                return HttpResponse('An error has occurred.')

            response = response.json()
            if int(response['count']) == 0:
                book, created = Book.objects.get_or_create(isbn=isbn)
                if created:
                    print('Book {} not found... (but created new record)'.format(isbn))
                else:
                    print('Book {} not found... (but found a record in db)'.format(isbn))
            elif int(response['count']) >= 2:
                print('More than 1 books with ISBN {} found!')
            elif int(response['count']) == 1:
                data = response['Items'][0]
                title = data['Item']['title'] + ' ' + data['Item']['subTitle'] + ' ' + data['Item']['contents']
                title = title.strip()
                book, created = Book.objects.get_or_create(isbn=data['Item']['isbn'])
                if created:
                    book.book_data_set.create(
                        provider = Provider.objects.get(slug=options['provider']),
                        title = title,
                        author = data['Item']['author'],
                        publisher = data['Item']['publisherName'],
                        cover = data['Item']['largeImageUrl'],
                    )
                    print('Both a book and the data "{}" created!'.format(title))
                else:
                    book_data, data_created = book.book_data_set.get_or_create(
                        provider = Provider.objects.get(slug=options['provider']),
                        defaults = {
                            'title': title,
                            'author': data['Item']['author'],
                            'publisher': data['Item']['publisherName'],
                            'cover': data['Item']['largeImageUrl'],
                        }
                    )
                    if data_created:
                        print('Book already exists, but book data for "{}" created!'.format(title))
                    else:
                        print('Book already exsits. Skipping...'.format(title))
