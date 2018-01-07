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

        self.upload_bucket = get_env('INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET')
        self.cache_bucket = get_env('INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET')
        self.output_bucket = get_env('INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET')

    def upload_project(self, stream, key):
        client = self._get_client()
        client.put_object(Body=stream,
                          Bucket=self.upload_bucket,
                          Key=key)

    def upload_cache(self, stream, key):
        client = self._get_client()
        client.put_object(Body=stream,
                          Bucket=self.cache_bucket,
                          Key=key)

    def upload_output(self, stream, key):
        client = self._get_client()
        client.put_object(Body=stream,
                          Bucket=self.output_bucket,
                          Key=key)

    def download_source(self, key):
        return self._download(self.upload_bucket, key)

    def download_output(self, key):
        return self._download(self.output_bucket, key)

    def download_cache(self, key):
        return self._download(self.cache_bucket, key)

    def _download(self, bucket, key):
        client = self._get_client()
        try:
            result = client.get_object(Bucket=bucket,
                                       Key=key)
        except Exception as e:
            print e
            return None

        path = '/tmp/%s_%s' % (uuid.uuid4(), key)
        with open(path, 'w') as f:
            f.write(result['Body'].read())

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
    def upload_project(self, stream, key):
        bucket = get_env('INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET')
        self._upload(stream, bucket, key)

    def upload_cache(self, stream, key):
        bucket = get_env('INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET')
        self._upload(stream, bucket, key)

    def upload_output(self, stream, key):
        bucket = get_env('INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET')
        self._upload(stream, bucket, key)


    def download_source(self, key):
        bucket = get_env('INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET')
        return self._download(bucket, key)

    def download_output(self, key):
        bucket = get_env('INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET')
        return self._download(bucket, key)

    def download_cache(self, key):
        bucket = get_env('INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET')
        return self._download(bucket, key)

    def _upload(self, stream, bucket, key):
        client = gcs.Client(project=get_env('INFRABOX_STORAGE_GCS_PROJECT_ID'))
        bucket = client.get_bucket(bucket)
        blob = bucket.blob(key)
        blob.upload_from_file(stream)

    def _download(self, bucket, key):
        client = gcs.Client(project=get_env('INFRABOX_STORAGE_GCS_PROJECT_ID'))
        bucket = client.get_bucket(bucket)
        blob = bucket.get_blob(key)

        if not blob:
            return None

        path = '/tmp/%s_%s' % (uuid.uuid4(), key)
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
