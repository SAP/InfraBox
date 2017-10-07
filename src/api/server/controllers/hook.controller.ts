"use strict";

const crypto = require('crypto');

import Promise = require("bluebird");
import { config } from "../config/config";
import { Request, Response, Router } from "express";
import { db, pgp, handleDBError } from "../db";
import { OK, BadRequest, NotFound } from "../utils/status";
import { logger } from "../utils/logger";
import * as request from 'request-promise';

const router = Router();
module.exports = router;

function signBlob(key, blob) {
    const s = 'sha1=' + crypto.createHmac('sha1', key).update(blob).digest('hex');
    return s;
}

router.post("/", (req: Request, res: Response, next) => {
    const event: String = req.headers['x-github-event'];

    if (!event) {
        return next(new BadRequest("No x-github-event found"));
    }

    const sig = req.headers['x-hub-signature'];

    if (!sig) {
        return next(new BadRequest("No x-hub-signature found"));
    }

    const options = {
        method: 'POST',
        uri: `http://${config.github.trigger_host}:8083/api/v1/trigger`,
        body: req.body,
        headers: {
            'x-github-event': event,
            'x-hub-signature': sig
        },
        json: true
    };

    request(options)
        .then(() => {
        OK(res, "ok");
    })
    .catch((err) => {
        next(new NotFound());
    });
});
