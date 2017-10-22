import { isUUID } from "./uuid";
import { NotFound, InternalError } from "./status";

const validators = {
    project_id: isUUID,
    build_id: isUUID,
    job_id: isUUID,
    user_id: isUUID,
    commit_id: () => true,
    file_id: () => true,
    build_number: () => true,
    build_restart_counter: () => true,
    dep_id: isUUID,
    secret_id: isUUID,
    token_id: isUUID,
    subscription_id: isUUID,
};

export function param_validation(req, res, next) {
    const keys = Object.keys(req.params);
    for (const k of keys) {
        const value = req.params[k];

        const validator = validators[k];
        if (!validator) {
            return next(new InternalError(new Error("No validator found")));
        }

        if (!validator(value)) {
            return next(new NotFound());
        }
    }

    return next(null);
}
