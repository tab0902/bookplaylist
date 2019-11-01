import json
import logging
import multiprocessing
import re
import requests
import sys
import time
import traceback

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from main.models import Book

OPENBD_ENDPOINT = 'https://api.openbd.jp/v1/'


class Command(BaseCommand):
    help = 'Get book data by openBD API and update infomation in DB.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--size', '--chunk-size',
            type=int,
            nargs='?',
            default=10000,
            help='Size of chunk, Default is 10000.',
        )
        parser.add_argument(
            '--start', '--start-point',
            type=int,
            nargs='?',
            default=0,
            help='Specify starting index of chunk. Default is 0.',
        )

    def chunked(self, iterable, n):
        return [iterable[x:x + n] for x in range(0, len(iterable), n)]

    def get_coverage(self):
        return requests.get(OPENBD_ENDPOINT + 'coverage').json()

    def get_bibs(self, items):
        return requests.post(OPENBD_ENDPOINT + 'get', data={'isbn': ','.join(items)}).json()

    def _format_date(self, raw):
        if(len(raw) == 0):
            date = None
        elif(1 <= len(raw) <= 4):
            date = raw
        elif(5 <= len(raw) <= 6):
            month = int(raw[4:6])
            if(month <= 12):
                date = '{}/{}'.format(raw[:4], raw[4:6])
            else:
                date = raw[:4]
        else:
            month = int(raw[4:6])
            if(month <= 12):
                date = '{}/{}/{}'.format(raw[:4], raw[4:6], raw[6:8])
            else:
                date = raw[:4]
        return date

    def format_data(self, data):
        isbn = data['summary']['isbn']
        title = data['summary']['title'][:255]
        volume = data['summary']['volume'][:255]
        series = data['summary']['series'][:255]
        publisher = data['summary']['publisher'][:255]
        pubdate_tmp = data['summary']['pubdate']
        cover = data['summary']['cover'][:200]
        author = data['summary']['author'][:255]
        title_collation_key = None
        if 'collationkey' in data['onix']['DescriptiveDetail']['TitleDetail']['TitleElement']['TitleText']:
            title_collation_key = data['onix']['DescriptiveDetail']['TitleDetail']['TitleElement']['TitleText']['collationkey'][:255]

        pubdate_list = [re.sub('\D', '', x) for x in pubdate_tmp.split(',')]
        pubdate_list = [self._format_date(x) for x in pubdate_list if x != '']
        pubdate = ','.join(pubdate_list)

        format_data = {
            'isbn': isbn,
            'defaults': {
                'title': title or None,
                'title_collation_key': title_collation_key or None,
                'volume': volume or None,
                'series': series or None,
                'publisher': publisher or None,
                'pubdate': pubdate or None,
                'cover': cover or None,
                'author': author or None,
            }
        }
        return format_data

    def handle(self, *args, **options):
        subject = 'Report of getbookdata command'
        body = 'Summary:\n\n'
        from_email = 'noreply@booxmix.com'
        to_email = ['admin@booxmix.com']
        coverage_start = options['start']
        chunk_size = options['size']

        cnt = cnt_created = coverage_start * chunk_size
        status = 'COMPLETE'
        start = time.time()

        print('Fetching coverage...')
        coverage = self.get_coverage()
        chunked_coverage = self.chunked(coverage, chunk_size)
        print('Done')
        print('\n----------------------------------------------------------------\n')

        for i, coverage_ in enumerate(chunked_coverage):
            print('Fetching data...')
            result = self.get_bibs(coverage_)
            print('Done')
            print('\n----------------------------------------------------------------\n')
            for bib in result:
                if bib and 'summary' in bib:
                    try:
                        book_data = self.format_data(bib)
                        book_obj, created = Book.objects.get_or_create(
                            isbn=book_data['isbn'],
                            defaults=book_data['defaults'],
                        )
                        if created:
                            cnt_created += 1
                        cnt += 1
                        created_ = 'T' if created else 'F'
                        print('{cnt} / {num}  |  time: {time}  |  created: {created}  |  pubdate: {pubdate}'.format(
                            cnt=cnt,
                            num=len(coverage),
                            time=int(time.time()-start),
                            created=created_,
                            pubdate=book_data['defaults']['pubdate']
                        ))
                    except Exception as e:
                        t, v, tb = sys.exc_info()
                        logging.exception(f'{e}')
                        status = 'ERROR'
                        body += '- Status: {}\n'.format(status)
                        body += '- Count all: {}\n'.format(cnt)
                        body += '- Count created: {}\n\n'.format(cnt_created)
                        body += '- Time: {}\n'.format(time.time()-start)
                        body += '- Data summary: \n{}\n\n'.format(json.dumps(bib['summary'], indent=2))
                        body += '- Exception: \n{}'.format(traceback.format_exc())
                        break
            else:
                continue
            break
            print('Done ()'.format(cnt=cnt, num=len(coverage)))
            print('Chunk: {cnt_chunk}/{num_chunk}'.format(cnt_chunk=i+1, num=len(chunked_coverage)))
            print('Count: {cnt}/{num}'.format(cnt=cnt, num=len(coverage)))
            print('\n----------------------------------------------------------------\n')

        if status == 'COMPLETE':
            body += '- Status: {}\n'.format(status)
            body += '- Count all: {}\n'.format(cnt)
            body += '- Count created: {}\n'.format(cnt_created)
            body += '- Time: {}\n'.format(time.time()-start)

        send_mail(subject, body, from_email, to_email)
