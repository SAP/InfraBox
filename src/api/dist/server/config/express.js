"use strict";
const logger_1 = require("../utils/logger");
const status_1 = require("../utils/status");
const uuid_1 = require("../utils/uuid");
const config_1 = require("../config/config");
const morgan = require("morgan");
const cookieParser = require("cookie-parser");
const bodyParser = require("body-parser");
const compress = require("compression");
const methodOverride = require("method-override");
const validator = require('express-validator');
module.exports = (app) => {
    const env = process.env.NODE_ENV || "development";
    app.locals.ENV = env;
    app.locals.ENV_DEVELOPMENT = env === "development";
    if (config_1.config.api.express.use_request_logger) {
        app.use(morgan("dev", { stream: logger_1.stream }));
    }
    app.use(bodyParser.json());
    app.use(bodyParser.urlencoded({
        extended: true
    }));
    app.use(validator({
        isUUID: uuid_1.isUUID
    }));
    app.use(cookieParser());
    app.use(compress());
    app.use(methodOverride());
    app.use('/v1', require('../controllers/routes'));
    app.get('/', (req, res) => {
        // used by other services to check if the server is already up
        res.json({});
    });
    app.get('/ping', (req, res) => {
        // used by other services to check if the server is already up
        res.json({});
    });
    app.use((req, res, next) => {
        next(new status_1.NotFound());
    });
    app.use((err, req, res, next) => {
        if (config_1.config.api.express.print_errors && !err.ignore_error) {
            logger_1.logger.error(err);
            if (err['details']) {
                logger_1.logger.error(err['details']);
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
