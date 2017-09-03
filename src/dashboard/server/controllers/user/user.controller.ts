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

router.get("/token", pv,(req: Request, res: Response, next) => {
    db.any('SELECT token, description, scope_push, scope_pull, id FROM "auth_token" where user_id = $1',
        [req['user'].id])
        .then((tokens: any[]) => {
            res.json(tokens);
        }).catch(handleDBError(next));
});

let AuthTokenSchema = {
    id: "/AuthTokenSchema",
    type: "object",
    properties: {
        description: { type: "string" },
        scope_pull: { type: "boolean" },
        scope_push: { type: "boolean" },
    },
    required: ["description", "scope_pull", "scope_push"]
};

router.post("/token", pv, (req: Request, res: Response, next) => {
    let user_id = req['user'].id;

    let v = new Validator();
    let envResult = v.validate(req['body'], AuthTokenSchema);

    if (envResult.errors.length > 0) {
        return next(new BadRequest("Invalid values"));
    }

    let description = req['body']['description'];
    let scope_push = req['body']['scope_push'];
    let scope_pull = req['body']['scope_pull'];

    db.none(`INSERT INTO auth_token (description, scope_push, scope_pull, user_id)
            VALUES ($1, $2, $3, $4)`,
        [description, scope_push, scope_pull, user_id])
    .then(() => {
        return OK(res, "Successfully added token");
    }).catch(handleDBError(next));
});

router.delete("/token/:token_id", pv, (req: Request, res: Response, next) => {
    let token_id = req.params['token_id'];
    let user_id = req['user'].id;

    db.none('DELETE FROM auth_token WHERE user_id = $1 and id = $2',
        [user_id, token_id])
        .then(() => {
            return OK(res, "Successfully deleted token");
        }).catch(handleDBError(next));
});


