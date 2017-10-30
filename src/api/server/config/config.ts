"use strict";

import path = require("path");
import { Validator } from 'jsonschema';

const rootPath = path.normalize(__dirname + "/..");
const env = process.env.NODE_ENV || "development";

function getFromEnv(name, def = null) {
    if (process.env[name]) {
        return process.env[name];
    }

    if (def !== null) {
        return def;
    }

    console.error(name + " not set");
    process.exit(1);
}

function getFromEnvBool(name, def: boolean = null): boolean {
    if (process.env[name]) {
        return process.env[name] === 'true';
    }

    if (def !== null) {
        return def;
    }

    console.error(name + " not set");
    process.exit(1);
}

export let config = {
    // local values
    root: rootPath,
    service: {
        name: getFromEnv("INFRABOX_NAME", "api"),
        version: getFromEnv("INFRABOX_VERSION", "local"),
    },
    database: {
        host: getFromEnv("INFRABOX_DATABASE_HOST"),
        port: getFromEnv("INFRABOX_DATABASE_PORT"),
        db: getFromEnv("INFRABOX_DATABASE_DB"),
        user: getFromEnv("INFRABOX_DATABASE_USER"),
        password: getFromEnv("INFRABOX_DATABASE_PASSWORD")
    },
    api: {
        url: getFromEnv("INFRABOX_API_URL"),
        port: getFromEnv("INFRABOX_API_PORT"),
        express: {
            use_request_logger: true,
            print_errors: true
        },
        log: {
            level: getFromEnv("INFRABOX_API_LOG_LEVEL", "info"),
            stackdriver: getFromEnvBool("INFRABOX_GENERAL_LOG_STACKDRIVER", false),
        },
        tls: {
            enabled: getFromEnvBool("INFRABOX_API_TLS_ENABLED", false),
            key: "",
            cert: ""
        }
    },
    github: {
        enabled: getFromEnvBool("INFRABOX_GITHUB_ENABLED", false),
        trigger_host: getFromEnv("INFRABOX_GITHUB_TRIGGER_HOST", "localhost")
    },
    docker_registry: {
        url: getFromEnv("INFRABOX_DOCKER_REGISTRY_URL")
    },
    storage: {
        gcs: {
            enabled: getFromEnvBool("INFRABOX_STORAGE_GCS_ENABLED", false),
            project_id: "",
            container_output_bucket: "",
            container_content_cache_bucket: "",
            project_upload_bucket: ""
        },
        s3: {
            enabled: getFromEnvBool("INFRABOX_STORAGE_S3_ENABLED", false),
            container_output_bucket: "",
            container_content_cache_bucket: "",
            project_upload_bucket: "",
            endpoint: "",
            port: 0,
            secure: true,
            accessKey: "",
            secretKey: ""
        }
    }
};

if (env === 'test') {
    config.api.express.print_errors = false;
    config.api.express.use_request_logger = false;
}

if (config.storage.gcs.enabled) {
    config.storage.gcs.project_id = getFromEnv("INFRABOX_STORAGE_GCS_PROJECT_ID");
    config.storage.gcs.container_output_bucket = getFromEnv("INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET");
    config.storage.gcs.container_content_cache_bucket = getFromEnv("INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET");
    config.storage.gcs.project_upload_bucket = getFromEnv("INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET");
}

if (config.storage.s3.enabled) {
    config.storage.s3.container_content_cache_bucket = getFromEnv("INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET");
    config.storage.s3.container_output_bucket = getFromEnv("INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET");
    config.storage.s3.project_upload_bucket = getFromEnv("INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET");
    config.storage.s3.endpoint = getFromEnv("INFRABOX_STORAGE_S3_ENDPOINT");
    config.storage.s3.port = parseInt(getFromEnv("INFRABOX_STORAGE_S3_PORT"), 10);
    config.storage.s3.secure = getFromEnvBool("INFRABOX_STORAGE_S3_SECURE");
    config.storage.s3.accessKey = getFromEnv("INFRABOX_STORAGE_S3_ACCESS_KEY");
    config.storage.s3.secretKey = getFromEnv("INFRABOX_STORAGE_S3_SECRET_KEY");
}

if (!config.storage.s3.enabled && !config.storage.gcs.enabled) {
    console.error("No storage enabled");
    process.exit(1);
}

if (config.api.tls.enabled) {
    config.api.tls.key = getFromEnv("INFRABOX_API_TLS_KEY", "/var/run/infrabox/server.key");
    config.api.tls.cert = getFromEnv("INFRABOX_API_TLS_CERT", "/var/run/infrabox/server.crt");
}
