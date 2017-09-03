"use strict";
const uuid_1 = require("./uuid");
const status_1 = require("./status");
const db_1 = require("../db");
const logger_1 = require("./logger");
function token_auth(req, res, next) {
    try {
        const t = req.headers["auth-token"];
        if (!uuid_1.isUUID(t)) {
            logger_1.logger.debug("token_auth: received an invalid uuid as token");
            return next(new status_1.Unauthorized());
        }
        db_1.db.any(`
            SELECT at.user_id as id FROM auth_token at WHERE token = $1
        `, [t])
            .then((users) => {
            if (users.length !== 1) {
                logger_1.logger.debug("token_auth: Did not find a user with the provided token");
                return next(new status_1.Unauthorized());
            }
            req["user"] = users[0];
            return next();
        })
            .catch(db_1.handleDBError(next));
    }
    catch (e) {
        logger_1.logger.debug(e);
        return next(new status_1.Unauthorized());
    }
}
exports.token_auth = token_auth;
function socket_token_auth(token) {
    return db_1.db.any(`
        SELECT at.user_id as id FROM auth_token at WHERE token = $1
    `, [token])
        .then((users) => {
        if (users.length !== 1) {
            logger_1.logger.debug("socket_token_auth: Did not find a user with the provided token");
            throw new status_1.Unauthorized();
        }
        return users[0];
    });
}
exports.socket_token_auth = socket_token_auth;
function checkProjectAccess(req, res, next) {
    const user_id = req["user"].id;
    const project_id = req.params["project_id"];
    db_1.db.any(`
        SELECT * FROM collaborator WHERE user_id = $1 and project_id = $2
    `, [user_id, project_id]).then((r) => {
        if (r.length !== 1) {
            logger_1.logger.debug("checkProjectAccess: user not a collaborator");
            return next(new status_1.NotFound());
        }
        else {
            return next();
        }
    }).catch(db_1.handleDBError(next));
}
exports.checkProjectAccess = checkProjectAccess;
