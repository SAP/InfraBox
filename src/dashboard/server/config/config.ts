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
        name: getFromEnv("INFRABOX_NAME", "dashboard"),
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
        url: getFromEnv("INFRABOX_API_URL")
    },
    docs: {
        url: getFromEnv("INFRABOX_DOCS_URL")
    },
    dashboard: {
        url: getFromEnv("INFRABOX_DASHBOARD_URL"),
        port: getFromEnv("INFRABOX_DASHBOARD_PORT"),
        secret: getFromEnv("INFRABOX_DASHBOARD_SECRET"),
        express: {
            use_request_logger: false,
            print_errors: true
        },
        log: {
            level: getFromEnv("INFRABOX_DASHBOARD_LOG_LEVEL", "info"),
            stackdriver: getFromEnvBool("INFRABOX_GENERAL_LOG_STACKDRIVER", false),
        },
        tls: {
            enabled: getFromEnvBool("INFRABOX_DASHBOARD_TLS_ENABLED", false),
            key: "",
            cert: ""
        }
    },
    account: {
        signup: {
            enabled: getFromEnvBool("INFRABOX_ACCOUNT_SIGNUP_ENABLED", false),
        },
        ldap: {
            enabled: getFromEnvBool("INFRABOX_ACCOUNT_LDAP_ENABLED", false),
            dn: "",
            password: "",
            url: "",
            base: ""
        }
    },
    gerrit: {
        enabled: getFromEnvBool("INFRABOX_GERRIT_ENABLED", false),
    },
    github: {
        enabled: getFromEnvBool("INFRABOX_GITHUB_ENABLED", false),
        client_id: "someid",
        client_secret: "somesecret",
        webhook_secret: "somewebhook",
        login: {
            enabled: false,
            url: "https://github.com/login",
        },
        api_url: "https://api.github.com"
    },
    docker_registry: {
        url: getFromEnv("INFRABOX_DOCKER_REGISTRY_URL")
    },
    storage: {
        gcs: {
            enabled: getFromEnvBool("INFRABOX_STORAGE_GCS_ENABLED", false),
            project_id: "",
            container_content_cache_bucket: "",
            container_output_bucket: "",
        },
        s3: {
            enabled: getFromEnvBool("INFRABOX_STORAGE_S3_ENABLED", false),
            container_content_cache_bucket: "",
            container_output_bucket: "",
            endpoint: "",
            port: 0,
            secure: true,
            accessKey: "",
            secretKey: ""
        }
    }
};

if (env === 'test') {
    config.dashboard.express.print_errors = false;
    config.dashboard.express.use_request_logger = false;
}

if (config.storage.gcs.enabled) {
    config.storage.gcs.project_id = getFromEnv("INFRABOX_STORAGE_GCS_PROJECT_ID");
    config.storage.gcs.container_content_cache_bucket = getFromEnv("INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET");
    config.storage.gcs.container_output_bucket = getFromEnv("INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET");
}

if (config.storage.s3.enabled) {
    config.storage.s3.container_content_cache_bucket = getFromEnv("INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET");
    config.storage.s3.container_output_bucket = getFromEnv("INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET");
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

if (config.account.ldap.enabled) {
    config.account.ldap.url = getFromEnv("INFRABOX_ACCOUNT_LDAP_URL");
    config.account.ldap.dn = getFromEnv("INFRABOX_ACCOUNT_LDAP_DN");
    config.account.ldap.base = getFromEnv("INFRABOX_ACCOUNT_LDAP_BASE");
    config.account.ldap.password = getFromEnv("INFRABOX_ACCOUNT_LDAP_PASSWORD");
}

if (config.github.enabled) {
    config.github.client_id = getFromEnv("INFRABOX_GITHUB_CLIENT_ID");
    config.github.client_secret = getFromEnv("INFRABOX_GITHUB_CLIENT_SECRET");
    config.github.webhook_secret = getFromEnv("INFRABOX_GITHUB_WEBHOOK_SECRET");
    config.github.login.url = getFromEnv("INFRABOX_GITHUB_LOGIN_URL");
    config.github.login.enabled = getFromEnvBool("INFRABOX_GITHUB_LOGIN_ENABLED", false);
    config.github.api_url = getFromEnv("INFRABOX_GITHUB_API_URL");
}

if (config.account.ldap.enabled && config.github.login.enabled) {
    console.error("Choose either account.ldap or github.login.enabled, but both together is not supported!");
    process.exit(1);
}

if (config.account.ldap.enabled && config.account.signup.enabled) {
    console.error("Choose either account.ldap or account.signup, but both together is not supported!");
    process.exit(1);
}

if (config.dashboard.tls.enabled) {
    config.dashboard.tls.key = getFromEnv("INFRABOX_DASHBOARD_TLS_KEY", "/var/run/infrabox/server.key");
    config.dashboard.tls.cert = getFromEnv("INFRABOX_DASHBOARD_TLS_CERT", "/var/run/infrabox/server.crt");
}
