#pylint: disable=too-few-public-methods
import os
import uuid

import boto3
from botocore.errorfactory import ClientError
from google.cloud import storage as gcs
from flask import after_this_request
from flask import _app_ctx_stack as stack
from azure.storage.blob import BlockBlobService
from keystoneauth1 import session
from keystoneauth1.identity import v3
from swiftclient.client import Connection, ClientException

from pyinfraboxutils import get_env

USE_S3 = get_env('INFRABOX_STORAGE_S3_ENABLED') == 'true'
USE_GCS = get_env('INFRABOX_STORAGE_GCS_ENABLED') == 'true'
USE_AZURE = get_env('INFRABOX_STORAGE_AZURE_ENABLED') == 'true'
USE_SWIFT = get_env('INFRABOX_STORAGE_SWIFT_ENABLED') == 'true'
storage = None

class Storage(object):
    def __init__(self):
        return

    def _upload(self, stream, key):
        return

    def _download(self, key):
        return

    def _delete(self, key):
        return

    def _clean_up(self, path):
        if not stack.top:
            return
        # inside a flask request
        @after_this_request
        def _remove_file(response):
            if os.path.exists(path):
                os.remove(path)
            return response

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

    def exists(self, key):
        return

class S3(Storage):
    def __init__(self):
        super(Storage, self).__init__()

        if get_env('INFRABOX_STORAGE_S3_SECURE') == 'true':
            url = 'https://'
        else:
            url = 'http://'
        url += get_env('INFRABOX_STORAGE_S3_ENDPOINT')
        url += ':'
        url += get_env('INFRABOX_STORAGE_S3_PORT')
        self.url = url

        self.bucket = get_env('INFRABOX_STORAGE_S3_BUCKET')
        self.create_buckets()

    def exists(self, key):
        client = self._get_client()
        try:
            client.head_object(Bucket=self.bucket, Key=key)
        except ClientError:
            return False
        return True

    def _upload(self, stream, key):
        client = self._get_client()
        client.put_object(Body=stream,
                          Bucket=self.bucket,
                          Key=key)

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

        path = '/tmp/%s' % uuid.uuid4()
        with open(path, 'w+') as f:
            f.write(result['Body'].read())

        self._clean_up(path)

        return path

    def _get_client(self):
        client = boto3.client('s3',
                              endpoint_url=self.url,
                              config=boto3.session.Config(signature_version='s3v4'),
                              aws_access_key_id=get_env('INFRABOX_STORAGE_S3_ACCESS_KEY'),
                              aws_secret_access_key=get_env('INFRABOX_STORAGE_S3_SECRET_KEY'))

        return client

class GCS(Storage):
    def __init__(self):
        super(Storage, self).__init__()
        self.bucket = get_env('INFRABOX_STORAGE_GCS_BUCKET')

    def _delete(self, key):
        try:
            client = gcs.Client()
            bucket = client.get_bucket(self.bucket)
            blob = bucket.blob(key)
            blob.delete()
        except:
            pass

    def exists(self, key):
        client = gcs.Client()
        bucket = client.get_bucket(self.bucket)
        blob = bucket.blob(key)
        return blob.exists()

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

        path = '/tmp/%s' % uuid.uuid4()
        with open(path, 'w+') as f:
            blob.download_to_file(f)

        self._clean_up(path)

        return path

class AZURE(Storage):
    def __init__(self):
        super(Storage, self).__init__()
        self.container = 'infrabox'

    def exists(self, key):
        client = self._get_client()
        return client.exists(container_name=self.container, blob_name=key)

    def _upload(self, stream, key):
        client = self._get_client()
        if not client.exists(container_name=self.container):
            client.create_container(container_name=self.container)
        client.create_blob_from_stream(container_name=self.container,
                                       blob_name=key,
                                       stream=stream)

    def _delete(self, key):
        client = self._get_client()
        try:
            client.delete_blob(container_name=self.container,
                               blob_name=key)
        except:
            pass

    def _download(self, key):
        client = self._get_client()
        path = '/tmp/%s' % uuid.uuid4()
        try:
            client.get_blob_to_path(container_name=self.container,
                                    blob_name=key,
                                    file_path=path)
        except:
            return None

        self._clean_up(path)

        return path

    def _get_client(self):
        client = BlockBlobService(account_name=get_env('INFRABOX_STORAGE_AZURE_ACCOUNT_NAME'),
                                  account_key=get_env('INFRABOX_STORAGE_AZURE_ACCOUNT_KEY'))
        return client

class SWIFT(Storage):
    def __init__(self):
        super(Storage, self).__init__()
        self.container = get_env('INFRABOX_STORAGE_SWIFT_CONTAINER_NAME')
        self.auth_url = get_env('INFRABOX_STORAGE_SWIFT_AUTH_URL')
        self.user_domain_name = get_env('INFRABOX_STORAGE_SWIFT_USER_DOMAIN_NAME')
        self.project_name = get_env('INFRABOX_STORAGE_SWIFT_PROJECT_NAME')
        self.project_domain_name = get_env('INFRABOX_STORAGE_SWIFT_PROJECT_DOMAIN_NAME')

    def exists(self, key):
        client = self._get_client()
        try:
            client.head_object(self.container, key)
        except ClientException:
            return False
        return True

    def _upload(self, stream, key):
        client = self._get_client()
        try:
            client.head_container(self.container)
        except ClientException:
            client.put_container(self.container)
        client.put_object(container=self.container,
                          obj=key,
                          contents=stream)

    def _delete(self, key):
        client = self._get_client()
        try:
            client.delete_object(container=self.container,
                                 obj=key)
        except:
            pass

    def _download(self, key):
        client = self._get_client()
        path = '/tmp/%s' % uuid.uuid4()
        try:
            _, contents = client.get_object(self.container, key)
            with open(path, 'w') as f:
                f.write(contents)
        except:
            return None

        self._clean_up(path)

        return path

    def _get_client(self):
        auth = v3.Password(auth_url=self.auth_url,
                           username=os.getenv('INFRABOX_STORAGE_SWIFT_USERNAME'),
                           password=os.getenv('INFRABOX_STORAGE_SWIFT_PASSWORD'),
                           user_domain_name=self.user_domain_name,
                           project_name=self.project_name,
                           project_domain_name=self.project_domain_name)
        keystone_session = session.Session(auth=auth)
        return Connection(session=keystone_session)

if USE_S3:
    storage = S3()
elif USE_GCS:
    get_env('GOOGLE_APPLICATION_CREDENTIALS')
    storage = GCS()
elif USE_AZURE:
    storage = AZURE()
elif USE_SWIFT:
    storage = SWIFT()
else:
    raise Exception('Unhandled storage type')
