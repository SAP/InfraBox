const passport = require('passport');
const GitHubStrategy = require('passport-github').Strategy;
const jwt = require("jsonwebtoken");
const fs = require('fs');

import { Router } from "express";
import { db, handleDBError } from "../../db";
import { config } from "../../config/config";
import { getEmail } from "../../utils/github";
import { auth, parseCookies } from "../../utils/auth";
import { NotFound } from "../../utils/status";
import { logger } from "../../utils/logger";

const router = Router();
module.exports = router;

const GITHUB_CLIENT_ID = config.github.client_id;
const GITHUB_CLIENT_SECRET = config.github.client_secret;
const GITHUB_CALLBACK_URL = config.dashboard.url + "/github/auth/callback";
const GITHUB_AUTHORIZATION_URL = config.github.login.url + "/oauth/authorize";
const GITHUB_TOKEN_URL = config.github.login.url + "/oauth/access_token";
const GITHUB_USER_PROFILE_URL = config.github.api_url + "/user";

passport.use(new GitHubStrategy({
    clientID: GITHUB_CLIENT_ID,
    clientSecret: GITHUB_CLIENT_SECRET,
    callbackURL: GITHUB_CALLBACK_URL,
    authorizationURL: GITHUB_AUTHORIZATION_URL,
    tokenURL: GITHUB_TOKEN_URL,
    userProfileURL: GITHUB_USER_PROFILE_URL,
    passReqToCallback: true
}, (req, accessToken, refreshToken, p, cb) => {
    p = p._json;

    let user = null;

    if (config.github.login.enabled) {
        db.tx((tx) => {
            return tx.any('SELECT id FROM "user" WHERE github_id = $1', [p.id])
            .then((users: any[]) => {
                if (users.length > 0) {
                    // user exists
                    return users[0];
                }

                // create user
                return tx.one(`
                    INSERT INTO "user" (github_id, username, avatar_url, name)
                    VALUES ($1, $2, $3, $4) RETURNING id
                `, [p.id, p.login, p.avatar_url, p.name]);
            })
            .then((u) => {
                user = u;
                return getEmail(accessToken);
            })
            .then((email) => {
                return tx.none('UPDATE "user" SET github_api_token = $1, email = $2 WHERE id = $3', [accessToken, email, user.id]);
            });
        })
        .then(() => {
            cb(null, user);
        })
        .catch(cb);
    } else {
        if (!req.query.t) {
            logger.debug("github callback: query param t not set");
            return cb(new NotFound());
        }

        auth(req, null, (err) => {
            if (err) {
                return cb(err);
            }

            const user_id = req['user'].id;
            db.tx((tx) => {
                return tx.any('SELECT id FROM "user" WHERE github_api_token = $1', [req.query.t])
                .then((users: any[]) => {
                    if (users.length !== 1) {
                        throw new NotFound();
                    }

                    user = users[0];

                    return tx.none(`UPDATE "user" SET github_api_token = $1, github_id = $2
                        WHERE id = $3`, [accessToken, p.id, user_id]);
                });
            })
            .then(() => {
                cb(null, user);
            })
            .catch(cb);
        });
    }
}));

if (config.github.login.enabled) {
    router.get('/', passport.authenticate('github', { scope: ['user:email', 'repo', 'read:org'] }));
} else {
    router.get('/connect', auth, (req, res, next) => {
        const user_id = req['user'].id;
        const uid = Math.random().toString(36).substr(2);

        db.none(`UPDATE "user" SET github_id = null, github_api_token = $1 WHERE id = $2`, [uid, user_id])
        .then(() => {
            const a = passport.authenticate('github', {
                scope: ['user:email', 'repo', 'read:org'],
                callbackURL: GITHUB_CALLBACK_URL + "?t=" + uid
            });

            a(req, res, next);
        })
        .catch(handleDBError(next));
    });
}

router.get('/callback',
    passport.authenticate('github', { failureRedirect: '/github/auth', session: false }),
    (req, res, next) => {
        const cert = fs.readFileSync('/var/run/secrets/infrabox.net/rsa/id_rsa');
        const token = jwt.sign({ user: req['user'], type: 'user' }, cert, { algorithm: 'RS256' });
        res.cookie("token", token);
        res.redirect('/dashboard/');
    }
);

