import { config } from "../config/config";

const storage = require('@google-cloud/storage');
const Minio = require('minio');

let deleteCacheImpl = null;
let downloadOutputImpl = null;

if (config.storage.gcs.enabled) {
    const gcs = storage({
        projectId: config.storage.gcs.project_id,
        keyFilename: '/etc/infrabox/gcs/gcs_service_account.json'
    });

    const cache_bucket = gcs.bucket(config.storage.gcs.container_content_cache_bucket);
    const output_bucket = gcs.bucket(config.storage.gcs.container_output_bucket);

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

    deleteCacheImpl = (file) => {
        return new Promise((resolve, reject) => {
            cache_bucket.file(file).delete(() => {
                resolve();
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

    deleteCacheImpl = (file) => {
        return new Promise((resolve, reject) => {
            minioClient.removeObject(config.storage.s3.container_content_cache_bucket, file, () => {
                resolve();
            });
        });
    };
}

export function deleteCache(file) {
    return deleteCacheImpl(file);
}

export function downloadOutput(file) {
    return downloadOutputImpl(file);
}
