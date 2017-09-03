"use strict";
const uuid_1 = require("./uuid");
const status_1 = require("./status");
const validators = {
    project_id: uuid_1.isUUID,
    build_id: uuid_1.isUUID,
    job_id: uuid_1.isUUID,
    user_id: uuid_1.isUUID,
    commit_id: () => true,
    dep_id: uuid_1.isUUID,
    secret_id: uuid_1.isUUID,
    token_id: uuid_1.isUUID,
    subscription_id: uuid_1.isUUID,
};
function param_validation(req, res, next) {
    const keys = Object.keys(req.params);
    for (const k of keys) {
        const value = req.params[k];
        const validator = validators[k];
        if (!validator) {
            return next(new status_1.InternalError(new Error("No validator found")));
        }
        if (!validator(value)) {
            return next(new status_1.NotFound());
        }
    }
    return next(null);
}
exports.param_validation = param_validation;
