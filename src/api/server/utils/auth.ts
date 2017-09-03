import { Request, Response } from "express";
import { config } from "../config/config";
import { isUUID } from "./uuid";
import { Unauthorized, NotFound } from "./status";
import { db, handleDBError } from "../db";
import { logger } from "./logger";

export function token_auth(req: Request, res: Response, next: any) {
    try {
        const t = req.headers["auth-token"];

        if (!isUUID(t)) {
            logger.debug("token_auth: received an invalid uuid as token");
            return next(new Unauthorized());
        }

        db.any(`
            SELECT at.user_id as id FROM auth_token at WHERE token = $1
        `, [t])
        .then((users: any[]) => {
            if (users.length !== 1) {
                logger.debug("token_auth: Did not find a user with the provided token");
                return next(new Unauthorized());
            }

            req["user"] = users[0];
            return next();
        })
        .catch(handleDBError(next));
    } catch (e) {
        logger.debug(e);
        return next(new Unauthorized());
    }
}

export function socket_token_auth(token: string) {
    return db.any(`
        SELECT at.user_id as id FROM auth_token at WHERE token = $1
    `, [token])
    .then((users: any[]) => {
        if (users.length !== 1) {
            logger.debug("socket_token_auth: Did not find a user with the provided token");
            throw new Unauthorized();
        }

        return users[0];
    });
}

export function checkProjectAccess(req: Request, res: Response, next: any) {
    const user_id = req["user"].id;
    const project_id = req.params["project_id"];

    db.any(`
        SELECT * FROM collaborator WHERE user_id = $1 and project_id = $2
    `, [user_id, project_id]
    ).then((r: any[]) => {
        if (r.length !== 1) {
            logger.debug("checkProjectAccess: user not a collaborator");
            return next(new NotFound());
        } else {
            return next();
        }
    }).catch(handleDBError(next));
}
