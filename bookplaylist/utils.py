import re
import requests
import time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from main.models import Provider


class APIMixin:

    def __init__(self, *args, **kwargs):
        self.provider = Provider.objects.get(slug=settings.DEFAULT_PROVIDER)
        return super().__init__(*args, **kwargs)

    def get_book_data(self, params):
        i = 0
        while i < 5:
            response = requests.get(self.provider.endpoint, params=params)
            if response.status_code in (requests.codes.ok, requests.codes.bad_request,):
                break
            else:
                i += 1
                time.sleep(1)
                continue
        return response

    def format_isbn(self, isbn):
        return re.sub(r'\D', '', isbn)

    def format_title(self, *args):
        return re.sub('  ', ' ', ' '.join(args).strip())


class SendEmailMixin:

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()
