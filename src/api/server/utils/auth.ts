import { Request, Response } from "express";
import { config } from "../config/config";
import { isUUID } from "./uuid";
import { Unauthorized, NotFound } from "./status";
import { db, handleDBError } from "../db";
import { logger } from "./logger";

export class Scopes {
    constructor(public push: boolean, public pull: boolean) {}
}

export class ProjectToken {
    constructor(public project_id: string, public scopes: Scopes) {}
}

export function token_auth(req: Request, res: Response, next: any) {
    try {
        const t = req.headers["auth-token"];

        if (!isUUID(t)) {
            logger.debug("token_auth: received an invalid uuid as token");
            return next(new Unauthorized());
        }

        db.any(`
            SELECT project_id, push, pull FROM auth_token at WHERE token = $1
        `, [t])
        .then((t: any[]) => {
            if (t.length !== 1) {
                logger.debug("token_auth: Did not find the token");
                return next(new Unauthorized());
            }


            const pt = t[0];
            req["token"] = new ProjectToken(pt.project_id, new Scopes(pt.push, pt.pull));
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
        SELECT project_id, push, pull FROM auth_token at WHERE token = $1
    `, [token])
    .then((t: any[]) => {
        if (t.length !== 1) {
            logger.debug("socket_token_auth: Did not find the token");
            throw new Unauthorized();
        }

        const pt = t[0]
        const project_token = new ProjectToken(pt.project_id, new Scopes(pt.push, pt.pull));
        return project_token;
    });
}

export function checkProjectAccess(req: Request, res: Response, next: any) {
    if (req.params['project_id'] === req['token']['project_id']) {
        return next();
    } else {
        return next(new NotFound());
    }
}
