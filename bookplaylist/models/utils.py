import emoji
import re


def camel_to_snake(string):
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)).lower()


def remove_emoji(raw_str):
    return ''.join(c for c in raw_str if c not in emoji.UNICODE_EMOJI)
