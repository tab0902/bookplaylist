from django.core.management.base import BaseCommand
from django.db.models import Q

from main.models import Playlist


class Command(BaseCommand):
    help = 'Create OGP image card of Playlist.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--override', '--force', '-f',
            action='store_true',
            help='Override existing cards. Default is False',
        )

    def handle(self, *args, **options):
        if options['override']:
            playlists = Playlist.objects.all()
        else:
            playlists = Playlist.objects.filter(Q(card=None) | Q(card=''))
        n = playlists.count()
        if not n:
            print('No data to create the card.')
        for i, playlist in enumerate(playlists):
            playlist.save_card()
            print('{i}/{n} Done. | title: {title}'.format(i=str(i+1).zfill(len(str(n))), n=n, title=playlist.title))
