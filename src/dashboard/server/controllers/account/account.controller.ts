const jwt = require("jsonwebtoken");
const bcrypt = require("bcryptjs");
const validator = require("validator");

import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { config } from "../../config/config";
import { logger } from "../../utils/logger";
import { BadRequest, OK } from "../../utils/status";

const router = Router();
module.exports = router;

function ErrorMessage(msg: string) {
    this.error_message = msg;
}

router.post("/login", (req: Request, res: Response, next) => {
    const email = req.body['email'];
    const password = req.body['password'];
    let user = null;

    db.any('SELECT id, password FROM "user" WHERE email = $1', [email]
    ).then((users: any[]) => {
        if (users.length !== 1) {
            throw new ErrorMessage("Invalid email/password combination");
        }
        user = users[0];

        return bcrypt.compare(password, users[0].password);
    }).then((valid_pw) => {
        if (!valid_pw) {
            throw new ErrorMessage("Invalid email/password combination");
        }

        const token = jwt.sign({ user: { id: user.id } }, config.dashboard.secret);
        res.cookie("token", token);
        return OK(res, "logged in successfully");
    })
    .catch((err) => {
        if (err.error_message) {
            return next(new BadRequest(err.error_message));
        } else {
            return next(new BadRequest("An internal error occured. Please try again later."));
        }
    });
});

router.post("/register", (req: Request, res: Response, next) => {
    const username = req.body['username'];
    const email = req.body['email'];
    const password1 = req.body['password1'];
    const password2 = req.body['password2'];

    let hash = null;
    let user = null;

    db.tx((tx) => {
        return bcrypt.hash(password1, 10).then((h) => {
            hash = h;

            if (password1 !== password2) {
                throw new ErrorMessage("Passwords don't match");
            }

            if (!validator.isEmail(email)) {
                throw new ErrorMessage("Not a valid email address");
            }

            if (!username || username.length < 4) {
                throw new ErrorMessage("Username too short");
            }

            if (!validator.isAlphanumeric(username)) {
                throw new ErrorMessage("Username must be alphanumeric");
            }

            return tx.any('SELECT id FROM "user" WHERE email = $1', [email]);
        }).then((users: any[]) => {
            if (users.length !== 0) {
                throw new ErrorMessage("An account with this email already esists");
            }

            return tx.one('insert into "user" (email, password) values ($1, $2) RETURNING ID',
                           [email, hash]);
        }).then((u) => {
            user = u;
            const token = jwt.sign({ user: { id: user.id } }, config.dashboard.secret);
            res.cookie("token", token);
            return OK(res, "logged in successfully");
        });
    })
    .catch((err) => {
        if (err.error_message) {
            return next(new BadRequest(err.error_message));
        } else {
            return next(new BadRequest("An internal error occured. Please try again later."));
        }
    });
});
