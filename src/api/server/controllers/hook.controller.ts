"use strict";

const crypto = require('crypto');
const bufferEq = require('buffer-equal-constant-time');

import Promise = require("bluebird");
import { config } from "../config/config";
import { Request, Response, Router } from "express";
import { db, pgp, handleDBError } from "../db";
import { OK, BadRequest } from "../utils/status";
import { logger } from "../utils/logger";
import { setStatus, getCommits } from "../utils/github";
import * as request from 'request-promise';

const router = Router();
module.exports = router;

function signBlob(key, blob) {
    const s = 'sha1=' + crypto.createHmac('sha1', key).update(blob).digest('hex');
    return s;
}

router.post("/", (req: Request, res: Response, next) => {
    // validate request
    const event: String = req.headers['x-github-event'];

    if (!event) {
        return next(new BadRequest("No x-github-event found"));
    }

    if (event === "ping") {
        return OK(res, "pong");
    }

    const sig = req.headers['x-hub-signature'];

    if (!sig) {
        return next(new BadRequest("No x-hub-signature found"));
    }

    const computedSig = new Buffer(signBlob(config.github.webhook_secret, JSON.stringify(req['body'])));

    if (!process.env.INFRABOX_TEST) {
        if (!bufferEq(new Buffer(sig), computedSig)) {
            return next(new BadRequest('X-Hub-Signature does not match blob signature'));
        }
    }

    const options = {
        method: 'POST',
        uri: 'http://localhost:8083/api/v1/trigger',
        body: req.body,
        headers: {
            'x-github-event': event,
            'x-hub-signature': sig
        },
        json: true
    }

    request(options)
        .then(() => {
        OK(res, "ok");
    })
    .catch(handleDBError(next));
});
