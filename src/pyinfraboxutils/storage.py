#pylint: disable=too-few-public-methods
import os
import uuid

import boto3
from google.cloud import storage as gcs
from flask import after_this_request

from pyinfraboxutils import get_env

USE_S3 = get_env('INFRABOX_STORAGE_S3_ENABLED') == 'true'
USE_GCS = get_env('INFRABOX_STORAGE_GCS_ENABLED') == 'true'
storage = None

class S3(object):
    def __init__(self):
        url = ''

        if get_env('INFRABOX_STORAGE_S3_SECURE') == 'true':
            url = 'https://'
        else:
            url = 'http://'
        url += get_env('INFRABOX_STORAGE_S3_ENDPOINT')
        url += ':'
        url += get_env('INFRABOX_STORAGE_S3_PORT')
        self.url = url

        self.bucket = get_env('INFRABOX_STORAGE_S3_BUCKET')

    def _upload(self, stream, key):
        client = self._get_client()
        client.put_object(Body=stream,
                          Bucket=self.bucket,
                          Key=key)

    def upload_project(self, stream, key):
        return self._upload(stream, 'upload/%s' % key)

    def upload_cache(self, stream, key):
        return self._upload(stream, 'cache/%s' % key)

    def upload_output(self, stream, key):
        return self._upload(stream, 'output/%s' % key)

    def upload_archive(self, stream, key):
        return self._upload(stream, 'archive/%s' % key)

    def download_source(self, key):
        return self._download('upload/%s' % key)

    def download_output(self, key):
        return self._download('output/%s' % key)

    def download_archive(self, key):
        return self._download('archive/%s' % key)

    def download_cache(self, key):
        return self._download('cache/%s' % key)

    def delete_cache(self, key):
        return self._delete('cache/%s' % key)

    def create_buckets(self):
        client = self._get_client()
        try:
            client.create_bucket(Bucket=self.bucket)
        except:
            pass

    def _delete(self, key):
        client = self._get_client()
        try:
            client.delete_object(Bucket=self.bucket,
                                 Key=key)
        except:
            pass


    def _download(self, key):
        client = self._get_client()
        try:
            result = client.get_object(Bucket=self.bucket,
                                       Key=key)
        except:
            return None

        path = '/tmp/%s_%s' % (uuid.uuid4(), key.replace('/', '_'))
        with open(path, 'w+') as f:
            f.write(result['Body'].read())

        if 'g' in globals():
            @after_this_request
            def _remove_file(response):
                if os.path.exists(path):
                    os.remove(path)
                return response

        return path

    def _get_client(self):
        client = boto3.client('s3',
                              endpoint_url=self.url,
                              config=boto3.session.Config(signature_version='s3v4'),
                              aws_access_key_id=get_env('INFRABOX_STORAGE_S3_ACCESS_KEY'),
                              aws_secret_access_key=get_env('INFRABOX_STORAGE_S3_SECRET_KEY'))

        return client

class GCS(object):
    def __init__(self):
        self.bucket = get_env('INFRABOX_STORAGE_GCS_BUCKET')


    def upload_project(self, stream, key):
        self._upload(stream, 'upload/%s' % key)

    def upload_cache(self, stream, key):
        self._upload(stream, 'cache/%s' % key)

    def upload_output(self, stream, key):
        self._upload(stream, 'output/%s' % key)

    def download_archive(self, key):
        return self._download('archive/%s' % key)

    def download_source(self, key):
        return self._download('upload/%s' % key)

    def download_output(self, key):
        return self._download('output/%s' % key)

    def download_cache(self, key):
        return self._download('cache/%s' % key)

    def delete_cache(self, key):
        return self._delete('cache/%s' % key)

    def _delete(self, key):
        client = gcs.Client()
        bucket = client.get_bucket(self.bucket)
        blob = bucket.blob(key)
        blob.delete()

    def _upload(self, stream, key):
        client = gcs.Client()
        bucket = client.get_bucket(self.bucket)
        blob = bucket.blob(key)
        blob.upload_from_file(stream)

    def _download(self, key):
        client = gcs.Client()
        bucket = client.get_bucket(self.bucket)
        blob = bucket.get_blob(key)

        if not blob:
            return None

        path = '/tmp/%s_%s' % (uuid.uuid4(), key.replace('/', '_'))
        with open(path, 'w+') as f:
            blob.download_to_file(f)

        @after_this_request
        def _remove_file(response):
            if os.path.exists(path):
                os.remove(path)
            return response

        return path

if USE_S3:
    storage = S3()
elif USE_GCS:
    get_env('GOOGLE_APPLICATION_CREDENTIALS')
    storage = GCS()
else:
    raise Exception('Unhandled storage type')
