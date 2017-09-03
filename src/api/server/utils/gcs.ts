import { config } from "../config/config";

const storage = require('@google-cloud/storage');
const Minio = require('minio');

let downloadOutputImpl = null;
let uploadProjectImpl = null;

if (config.storage.gcs.enabled) {
    const gcs = storage({
        projectId: config.storage.gcs.project_id,
        keyFilename: '/etc/infrabox/gcs/gcs_service_account.json'
    });

    const output_bucket = gcs.bucket(config.storage.gcs.container_output_bucket);
    const upload_bucket = gcs.bucket(config.storage.gcs.project_upload_bucket);

    downloadOutputImpl = (file) => {
        return new Promise((resolve, reject) => {
            try {
                const stream = output_bucket.file(file).createReadStream();
                resolve(stream);
            } catch (err) {
                reject(err);
            }
        });
    };

    uploadProjectImpl = (localPath, destination) => {
        return new Promise((resolve, reject) => {
            upload_bucket.upload(localPath, { destination: destination }, (err) => {
                if (err) {
                    reject(err);
                } else {
                    resolve();
                }
            });
        });
    };
} else if (config.storage.s3.enabled) {
    const minioClient = new Minio.Client({
        endPoint: config.storage.s3.endpoint,
        port: config.storage.s3.port,
        secure: config.storage.s3.secure,
        accessKey: config.storage.s3.accessKey,
        secretKey: config.storage.s3.secretKey
    });

    downloadOutputImpl = (file) => {
        return new Promise((resolve, reject) => {
            minioClient.getObject(config.storage.s3.container_output_bucket,
                                  file, (err, stream) => {
                if (err) {
                    if (err.code == 'NoSuchKey') {
                        resolve(null);
                    } else {
                        reject(err);
                    }
                } else {
                    resolve(stream);
                }
            });
        });
    };

    uploadProjectImpl = (localPath, destination) => {
        return new Promise((resolve, reject) => {
            minioClient.fPutObject(config.storage.s3.project_upload_bucket,
                                   destination, localPath,
                                   'application/octet-stream', (err) => {
                if (err) {
                    reject(err);
                } else {
                    resolve();
                }
            });
        });
    };
}

export function downloadOutput(file) {
    return downloadOutputImpl(file);
}

export function uploadProject(localPath, destination) {
    return uploadProjectImpl(localPath, destination);
}
