#pylint: disable=too-few-public-methods,redefined-variable-type
import boto3

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

    def upload_project(self, stream, key):
        client = self.get_client()
        client.put_object(Body=stream,
                          Bucket=self.upload_bucket,
                          Key=key)

    def get_client(self):
        client = boto3.client('s3',
                              endpoint_url=self.url,
                              config=boto3.session.Config(signature_version='s3v4'),
                              aws_access_key_id=get_env('INFRABOX_STORAGE_S3_ACCESS_KEY'),
                              aws_secret_access_key=get_env('INFRABOX_STORAGE_S3_SECRET_KEY'))

        return client

class GCS(object):
    def upload_project(self):
        pass

if USE_S3:
    storage = S3()
elif USE_GCS:
    storage = GCS()
else:
    raise Exception('Unhandled storage type')
