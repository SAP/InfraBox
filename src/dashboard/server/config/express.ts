"use strict";

import express = require("express");
import { logger, stream } from "../utils/logger";
import { NotFound, InternalError } from "../utils/status";
import { config } from "../config/config";
import { isUUID } from "../utils/uuid";

const morgan = require("morgan");
const cookieParser = require("cookie-parser");
const bodyParser = require("body-parser");
const compress = require("compression");
const methodOverride = require("method-override");
const passport = require("passport");
const validator = require('express-validator');

module.exports = (app) => {
    const env = process.env.NODE_ENV || "development";
    app.locals.ENV = env;
    app.locals.ENV_DEVELOPMENT = env === "development";

    if (config.dashboard.express.use_request_logger) {
        app.use(morgan("dev", { stream: stream }));
    }

    app.use(bodyParser.json());
    app.use(bodyParser.urlencoded({
        extended: true
    }));
    app.use(validator({
        isUUID: isUUID
    }));
    app.use(cookieParser());
    app.use(passport.initialize());
    app.use(compress());
    app.use(methodOverride());

    app.use('/api/dashboard/project', require('../controllers/project/routes'));
    app.use('/api/dashboard/user', require('../controllers/user/routes'));
    app.use('/api/dashboard/account', require('../controllers/account/routes'));

    app.use('/api/dashboard/account', require('../controllers/account/routes'));

    if (config.github.enabled) {
        app.use('/api/dashboard/github', require('../controllers/github/repos.controller'));
        app.use('/github/auth', require('../controllers/github/routes'));
    }

    app.get('/api/dashboard/settings', (req, res) => {
        res.json({
            INFRABOX_GITHUB_ENABLED: config.github.enabled,
            INFRABOX_GERRIT_ENABLED: config.gerrit.enabled,
            INFRABOX_ACCOUNT_SIGNUP_ENABLED: config.account.signup.enabled,
            INFRABOX_ACCOUNT_LDAP_ENABLED: config.account.ldap.enabled
        });
    });

    app.get('/', (req, res) => {
        res.json({});
    });

    app.get('/ping', (req, res) => {
        // used by other services to check if the server is already up
        res.json({});
    });

    app.use((req, res, next) => {
        next(new NotFound());
    });

    app.use((err, req, res, next) => {
        if (config.dashboard.express.print_errors && !err.ignore_error) {
            logger.error(err);
            if (err['details']) {
                logger.error(err['details']);
            }
        }

        let message = err['message'];
        if (!err.infrabox_error) {
            message = 'Internal Server Error';
        }

        res.status(err.status || 500);
        res.json({ message: message, type: "error" });
    });
};
