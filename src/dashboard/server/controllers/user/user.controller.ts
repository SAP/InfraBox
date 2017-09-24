import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { NotFound, BadRequest, OK } from "../../utils/status";
import { Validator } from 'jsonschema';
import { param_validation as pv } from "../../utils/validation";

let router = Router();
module.exports = router;

router.get("/", pv, (req: Request, res: Response, next) => {
    db.any('SELECT github_id, username, avatar_url, name, created_at, email FROM "user" where id = $1',
        [req['user'].id])
        .then((users: any[]) => {
            if (users.length !== 1) {
                return next(new NotFound());
            }
            res.json(users[0]);
        }).catch(handleDBError(next));
});


