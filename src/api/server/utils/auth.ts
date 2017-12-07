import { Request, Response } from "express";
import { config } from "../config/config";
import { isUUID } from "./uuid";
import { Unauthorized, NotFound } from "./status";
import { db, handleDBError } from "../db";
import { logger } from "./logger";

const jwt = require('jsonwebtoken');
const fs = require('fs');

export class Scopes {
    constructor(public push: boolean, public pull: boolean) {}
}

export class ProjectToken {
    constructor(public id: string, public project_id: string, public scopes: Scopes) {}
}

export function token_auth(req: Request, res: Response, next: any) {
    try {
        const t = req.headers["authorization"];

        if (!t) {
            logger.warn("token_auth: Authorization header not set");
            return next(new Unauthorized());
        }

        const parts = t.split(' ');
        if (parts[0] !== 'token') {
            logger.warn("token_auth: does not start with token");
            return next(new Unauthorized());
        }

        const cert = fs.readFileSync('/var/run/secrets/infrabox.net/rsa/id_rsa.pub');
        const token = jwt.verify(parts[1], cert, { algorithms: ['RS256'] });

        db.any(`
            SELECT project_id
            FROM auth_token at
            WHERE id = $1 AND project_id = $2
        `, [token.id, token.project.id])
        .then((result: any[]) => {
            if (result.length !== 1) {
                logger.warn("token_auth: Did not find the token");
                return next(new Unauthorized());
            }

            req["token"] = new ProjectToken(token.id, token.project.id,
                                            new Scopes(token.scope.push, token.scope.pull));
            return next();
        })
        .catch(handleDBError(next));
    } catch (e) {
        logger.warn(e);
        return next(new Unauthorized());
    }
}

export function socket_token_auth(t: string) {
    const cert = fs.readFileSync('/var/run/secrets/infrabox.net/rsa/id_rsa.pub');
    const token = jwt.verify(t, cert);

    return db.any(`
        SELECT project_id FROM auth_token at WHERE id = $1 AND project_id = $2
    `, [token])
    .then((result: any[]) => {
        if (result.length !== 1) {
            logger.warn("socket_token_auth: Did not find the token");
            throw new Unauthorized();
        }

        const project_token = new ProjectToken(token.id, token.project.id,
                                               new Scopes(token.scope.push, token.scope.pull));
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
