"use strict";
const config_1 = require("../config/config");
const storage = require('@google-cloud/storage');
const Minio = require('minio');
let downloadOutputImpl = null;
let uploadProjectImpl = null;
if (config_1.config.storage.gcs.enable) {
    const gcs = storage({
        projectId: config_1.config.storage.gcs.project_id,
        keyFilename: '/etc/infrabox/gcs/gcs_service_account.json'
    });
    const output_bucket = gcs.bucket(config_1.config.storage.gcs.container_output_bucket);
    const upload_bucket = gcs.bucket(config_1.config.storage.gcs.project_upload_bucket);
    downloadOutputImpl = (file) => {
        return new Promise((resolve, reject) => {
            try {
                const stream = output_bucket.file(file).createReadStream();
                resolve(stream);
            }
            catch (err) {
                reject(err);
            }
        });
    };
    uploadProjectImpl = (localPath, destination) => {
        return new Promise((resolve, reject) => {
            upload_bucket.upload(localPath, { destination: destination }, (err) => {
                if (err) {
                    reject(err);
                }
                else {
                    resolve();
                }
            });
        });
    };
}
else if (config_1.config.storage.s3.enable) {
    const minioClient = new Minio.Client({
        endPoint: config_1.config.storage.s3.endpoint,
        port: config_1.config.storage.s3.port,
        secure: config_1.config.storage.s3.secure,
        accessKey: config_1.config.storage.s3.accessKey,
        secretKey: config_1.config.storage.s3.secretKey
    });
    downloadOutputImpl = (file) => {
        return new Promise((resolve, reject) => {
            minioClient.getObject(config_1.config.storage.s3.container_output_bucket, file, (err, stream) => {
                if (err) {
                    reject(err);
                }
                else {
                    resolve(stream);
                }
            });
        });
    };
    uploadProjectImpl = (localPath, destination) => {
        return new Promise((resolve, reject) => {
            minioClient.fPutObject(config_1.config.storage.s3.project_upload_bucket, destination, localPath, 'application/octet-stream', (err) => {
                if (err) {
                    reject(err);
                }
                else {
                    resolve();
                }
            });
        });
    };
}
function downloadOutput(file) {
    return downloadOutputImpl(file);
}
exports.downloadOutput = downloadOutput;
function uploadProject(localPath, destination) {
    return uploadProjectImpl(localPath, destination);
}
exports.uploadProject = uploadProject;
