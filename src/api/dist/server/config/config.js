"use strict";
const path = require("path");
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
function getFromEnvBool(name, def = null) {
    if (process.env[name]) {
        return process.env[name] === 'true';
    }
    if (def !== null) {
        return def;
    }
    console.error(name + " not set");
    process.exit(1);
}
exports.config = {
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
            use_request_logger: false,
            print_errors: true
        },
        log: {
            level: getFromEnv("INFRABOX_API_LOG_LEVEL", "info"),
            stackdriver: getFromEnvBool("INFRABOX_API_LOG_STACKDRIVER", false),
        }
    },
    github: {
        enable: getFromEnvBool("INFRABOX_GITHUB_ENABLE", false),
        client_id: "someid",
        client_secret: "somesecret",
        webhook_secret: "somewebhook"
    },
    docker_registry: {
        url: getFromEnv("INFRABOX_DOCKER_REGISTRY_URL")
    },
    storage: {
        gcs: {
            enable: getFromEnvBool("INFRABOX_STORAGE_GCS_ENABLE", false),
            project_id: "",
            container_output_bucket: "",
            container_content_cache_bucket: "",
            project_upload_bucket: ""
        },
        s3: {
            enable: getFromEnvBool("INFRABOX_STORAGE_S3_ENABLE", false),
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
    exports.config.api.express.print_errors = false;
    exports.config.api.express.use_request_logger = false;
}
if (exports.config.storage.gcs.enable) {
    exports.config.storage.gcs.project_id = getFromEnv("INFRABOX_STORAGE_GCS_PROJECT_ID");
    exports.config.storage.gcs.container_output_bucket = getFromEnv("INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET");
    exports.config.storage.gcs.container_content_cache_bucket = getFromEnv("INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET");
    exports.config.storage.gcs.project_upload_bucket = getFromEnv("INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET");
}
if (exports.config.storage.s3.enable) {
    exports.config.storage.s3.container_content_cache_bucket = getFromEnv("INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET");
    exports.config.storage.s3.container_output_bucket = getFromEnv("INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET");
    exports.config.storage.s3.project_upload_bucket = getFromEnv("INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET");
    exports.config.storage.s3.endpoint = getFromEnv("INFRABOX_STORAGE_S3_ENDPOINT");
    exports.config.storage.s3.port = parseInt(getFromEnv("INFRABOX_STORAGE_S3_PORT"), 10);
    exports.config.storage.s3.secure = getFromEnvBool("INFRABOX_STORAGE_S3_SECURE");
    exports.config.storage.s3.accessKey = getFromEnv("INFRABOX_STORAGE_S3_ACCESS_KEY");
    exports.config.storage.s3.secretKey = getFromEnv("INFRABOX_STORAGE_S3_SECRET_KEY");
}
if (!exports.config.storage.s3.enable && !exports.config.storage.gcs.enable) {
    console.error("No storage enabled");
    process.exit(1);
}
if (exports.config.github.enable) {
    exports.config.github.client_id = getFromEnv("INFRABOX_GITHUB_CLIENT_ID");
    exports.config.github.client_secret = getFromEnv("INFRABOX_GITHUB_CLIENT_SECRET");
    exports.config.github.webhook_secret = getFromEnv("INFRABOX_GITHUB_WEBHOOK_SECRET");
}
