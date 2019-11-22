from storages.backends.gcloud import GoogleCloudStorage
from storages.utils import setting


class GoogleCloudMediaStorage(GoogleCloudStorage):

    def __init__(self, *args, **kwargs):
        kwargs['custom_endpoint'] = setting('GS_MEDIA_CUSTOM_ENDPOINT', None)
        kwargs['bucket_name'] = setting('GS_MEDIA_BUCKET_NAME')
        super().__init__(*args, **kwargs)


class GoogleCloudStaticStorage(GoogleCloudStorage):

    def __init__(self, *args, **kwargs):
        kwargs['custom_endpoint'] = setting('GS_STATIC_CUSTOM_ENDPOINT', None)
        kwargs['bucket_name'] = setting('GS_STATIC_BUCKET_NAME')
        super().__init__(*args, **kwargs)
