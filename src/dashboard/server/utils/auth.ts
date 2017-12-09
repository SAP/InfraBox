import { Request, Response } from "express";
import { config } from "../config/config";
import { isUUID } from "./uuid";
import { Unauthorized, NotFound } from "./status";
import { db, handleDBError } from "../db";
import { logger } from "./logger";

const jwt = require("jsonwebtoken");
const fs = require('fs');

export function parseCookies(request) {
    var list = {},
        rc = request.headers.cookie;

    rc && rc.split(';').forEach(function( cookie ) {
        var parts = cookie.split('=');
        list[parts.shift().trim()] = decodeURI(parts.join('='));
    });

    return list;
}

export function auth(req: Request, res: Response, next: any) {
    try {
        const cookies = parseCookies(req);
        const t = cookies["token"];
        const cert = fs.readFileSync('/var/run/secrets/infrabox.net/rsa/id_rsa.pub');
        const decoded = jwt.verify(t, cert, { algorithm: 'RS256' });

        if (!decoded.user) {
            logger.debug("auth: user not set");
            return next(new Unauthorized());
        }

        if (!isUUID(decoded.user.id)) {
            logger.debug("auth: user id not valid uuid");
            return next(new Unauthorized());
        }

        const user_id = decoded.user.id;

        db.any(`SELECT id as cnt FROM "user" WHERE id = $1`, [user_id])
            .then((r: any[]) => {

            if (r.length !== 1) {
                logger.debug("auth: user " + user_id + " does not exist");
                throw new Unauthorized();
            }

            req["user"] = decoded.user;
            return next();
        }).catch(handleDBError(next));
    } catch (e) {
        console.log(e);
        return next(new Unauthorized());
    }
}

export function socket_auth(token: string) {
    try {
        const cert = fs.readFileSync('/var/run/secrets/infrabox.net/rsa/id_rsa.pub');
        const decoded = jwt.verify(token, cert, { algorithm: 'RS256' });

        if (!decoded.user) {
            return null;
        }

        if (!isUUID(decoded.user.id)) {
            return null;
        }

        // TODO(Steffen): check user does exist

        return decoded.user;
    } catch (e) {
        return null;
    }
}

export function checkProjectAccess(req: Request, res: Response, next: any) {
    console.log("checkProjectAccess");
    const user_id = req['user'].id;
    const project_id = req.params['project_id'];

    db.any(`
        SELECT co.*
        FROM collaborator co
        INNER JOIN "user" u
            ON u.id = $1
            AND co.user_id = $1
            AND co.project_id = $2
    `, [user_id, project_id]
    ).then((r: any[]) => {
        if (r.length !== 1) {
            logger.debug("checkProjectAccess: user " + user_id + " has no access to project " + project_id);
            throw new NotFound();
        } else {
            logger.debug("checkProjectAccess: user " + user_id + " has access to project " + project_id);
            return next();
        }
    }).catch(handleDBError(next));
}

export function checkProjectAccessPublic(req: Request, res: Response, next: any) {
    const project_id = req.params['project_id'];

    try {
		const cookies = parseCookies(req);
        const t = cookies["token"];
        const cert = fs.readFileSync('/var/run/secrets/infrabox.net/rsa/id_rsa.pub');
        const decoded = jwt.verify(t, cert, { algorithm: 'RS256' });

        if (decoded.user && isUUID(decoded.user.id)) {
            req["user"] = decoded.user;
        }
    } catch (e) {
       logger.debug("checkProjectAccessPublic: project " + project_id + " received invalid token");
    }

    db.any(`
        SELECT public FROM project WHERE id = $1
    `, [project_id]
    ).then((result: any[]) => {
        if (result.length !== 1) {
            logger.debug("checkProjectAccessPublic: project " + project_id + " not found");
            throw new NotFound();
        }

        const r = result[0];

        if (r.public) {
            logger.debug("checkProjectAccessPublic: project " + project_id + " is public");
            return next();
        } else {
            if (req['user']) {
                return checkProjectAccess(req, res, next);
            } else {
                logger.debug("checkProjectAccessPublic: project " + project_id + " is neither public nor the user has access to it");
                throw new Unauthorized();
            }
        }
    }).catch(handleDBError(next));
}

export function checkProjectAccessPublicName(req: Request, res: Response, next: any) {
    const project_name = req.params['project_name'];

    try {
		const cookies = parseCookies(req);
        const t = cookies["token"];
        const cert = fs.readFileSync('/var/run/secrets/infrabox.net/rsa/id_rsa.pub');
        const decoded = jwt.verify(t, cert, { algorithm: 'RS256' });

        if (decoded.user && isUUID(decoded.user.id)) {
            req["user"] = decoded.user;
        }
    } catch (e) {
       logger.debug("checkProjectAccessPublicName: project " + project_name + " received invalid token");
    }

    db.any(`
        SELECT public FROM project WHERE name = $1
    `, [project_name]
    ).then((result: any[]) => {
        if (result.length !== 1) {
            logger.debug("checkProjectAccessPublicName: project " + project_name + " not found");
            throw new NotFound();
        }

        const r = result[0];

        if (r.public) {
            logger.debug("checkProjectAccessPublicName: project " + project_name + " is public");
            return next();
        } else {
            if (req['user']) {
                return checkProjectAccess(req, res, next);
            } else {
                logger.debug("checkProjectAccessPublicName: project " + project_name + " is neither public nor the user has access to it");
                throw new Unauthorized();
            }
        }
    }).catch(handleDBError(next));
}
