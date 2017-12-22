# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.test import Client
from django.utils.deconstruct import deconstructible
from django.utils.six.moves.urllib.parse import urlparse

from storages.backends.s3boto import S3BotoStorage

import mimetypes

mimetypes.types_map['.less']  = 'text/less'
mimetypes.types_map['.woff2'] = 'application/x-font-woff2'

REGIONS = {
    'us-east-1':      's3.amazonaws.com',
    'us-west-2':      's3-us-west-2.amazonaws.com',
    'us-west-1':      's3-us-west-1.amazonaws.com',
    'eu-west-1':      's3-eu-west-1.amazonaws.com',
    'eu-central-1':   's3.eu-central-1.amazonaws.com',
    'ap-southeast-1': 's3-ap-southeast-1.amazonaws.com',
    'ap-southeast-2': 's3-ap-southeast-2.amazonaws.com',
    'ap-northeast-1': 's3-ap-northeast-1.amazonaws.com',
    'sa-east-1':      's3-sa-east-1.amazonaws.com',
}

def build_s3_link(bucket, region = None):
    endpoint = REGIONS.get(region or settings.AWS_DEFAULT_REGION, 's3.amazonaws.com')
    return 'https://{0}/{1}'.format(endpoint, bucket)

def parse_aws_url(url):
    #return value ('', 'workflow-resource', 'workflow-resource.s3.eu-central-1.amazonaws.com', 'eu-central-1')
    url = urlparse(url)
    if url.netloc.startswith("s3."):
        #the url is a clean s3 bucket.
        #sample url //s3.eu-central-1.amazonaws.com/workflow-release-userfile/...
        return dict(
            url_protocol  = url.scheme,
            bucket_name   = url.path.split("/")[1],
            custom_domain = url.netloc + url.path,
            region        = url.netloc.split(".")[1],
            )

    #the url is an s3 with a subdomain
    bits = url.netloc.split(".")
    return dict(
        url_protocol  = url.scheme,
        bucket_name   = bits[0],
        custom_domain = url.netloc + url.path,
        region        = bits[2],
        )

@deconstructible
class S3Storage(S3BotoStorage):

    is_s3 = True
    secure_urls = False
    querystring_auth = False
    querystring_expire = False
    aws_url = None
    custom_url = None

    def __init__(self, aws_url = None, is_public = True, custom_url = None, *args, **kw):
        super(S3Storage, self).__init__(*args, **kw)
        for key, value in parse_aws_url(aws_url or self.aws_url).items():
            setattr(self, key, value)

        self.default_acl = is_public and 'public-read' or None
        self.custom_domain = custom_url or self.custom_url or self.custom_domain

    def save(self, name, content):
        return super(S3Storage, self).save(name, File(content))

    @property
    def connection(self):
        if self._connection is None:
            self._connection = self.connection_class(
                self.access_key, self.secret_key,
                calling_format=self.calling_format,
                host='s3.%s.amazonaws.com' % self.region
                )
        return self._connection

    def url(self, name):
        if not name:
            return
        if EXTERNAL_FILE_REGEX.match(name):
            return name
        return super(S3Storage, self).url(name)

class Command(BaseCommand):

    def handle(self, *args, **options):

        S3Storage(settings.AWS_DEPLOY_URL).save(
            'index.html',
            ContentFile(Client().get(reverse('app')).content)
        )

        self.stdout.write('https://%(bucket_name)s.s3-website.%(region)s.amazonaws.com' % parse_aws_url(settings.AWS_DEPLOY_URL))