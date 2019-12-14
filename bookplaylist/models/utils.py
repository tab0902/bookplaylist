import emoji
import re


def camel_to_snake(string):
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)).lower()


def get_file_path(instance, filename, field, filetype='img'):
    directory = os.path.join(filetype, instance.__class__._meta.db_table, field)
    filename = str(instance.pk) + os.path.splitext(filename)[-1]
    path = os.path.join(directory, filename)
    return path


def remove_emoji(raw_str):
    return ''.join(c for c in raw_str if c not in emoji.UNICODE_EMOJI)
