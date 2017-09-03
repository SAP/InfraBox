"use strict";

const jwt = require("jsonwebtoken");

import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { config } from "../../config/config";
import { logger } from "../../utils/logger";

const router = Router();
module.exports = router;

function authenticate(email, password) {
    const LdapAuth = require('ldapauth-fork');
    const opts = {
          url: config.account.ldap.url,
          bindDN: config.account.ldap.dn,
          bindCredentials: config.account.ldap.password,
          searchBase: config.account.ldap.base,
          searchFilter: '(mail={{username}})',
          reconnect: true
    };

    const ldap = new LdapAuth(opts);

    return new Promise((resolve, reject) => {
        ldap.authenticate(email, password, (err, user) => {
            if (err) {
                reject(err);
            } else {
                resolve(user);
            }

            ldap.close((err) => {
                if (err) {
                    logger.warn(err);
                }
            });
        });
    });
}

router.post("/login", (req: Request, res: Response, next) => {
    const email = req.body['email'];
    const password = req.body['password'];
    let ldapUser = null;
    let user = null;
    let created = false;

    db.tx((tx) => {
        return authenticate(email, password)
        .then((user: any) => {
            ldapUser = user;
            return tx.any('SELECT id FROM "user" WHERE email = $1', [email])
        })
        .then((users: any[]) => {
            if (users.length > 0) {
                // user exists
                return users[0];
            }

            created = true;
            // create user
            return tx.one(`
                INSERT INTO "user" (email, username, name)
                VALUES ($1, $2, $3) RETURNING id
            `, [email, ldapUser.cn, ldapUser.displayName]);
        })
        .then((u) => {
            user = u;

            // create user
            if (created) {
                return tx.any(`
                    INSERT INTO user_quota (user_id, max_concurrent_jobs, max_cpu_per_job,
                              max_memory_per_job, max_jobs_per_build)
                    VALUES ($1, 1, 1, 1024, 50)
                `, [u.id]);
            }
        })
        .then(() => {
            const token = jwt.sign({ user: { id: user.id } }, config.dashboard.secret);
            res.cookie("token", token);
            res.redirect('/dashboard/start');
        });
    })
    .catch((err) => {
        logger.warn(err);
        res.render("index", {
            message: "Invalid email/password combination",
            github_enabled: config.github.enabled
        });
    });
});
