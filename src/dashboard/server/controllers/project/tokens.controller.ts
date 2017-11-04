import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { BadRequest, OK } from "../../utils/status";
import { param_validation as pv } from "../../utils/validation";
import { Validator } from 'jsonschema';

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/", pv,(req: Request, res: Response, next) => {
    let project_id = req.params['project_id'];

    db.any(`SELECT token, description, scope_push, scope_pull, id
            FROM "auth_token" where project_id = $1`,
        [project_id])
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

router.post("/", pv, (req: Request, res: Response, next) => {
    let project_id = req.params['project_id'];

    let v = new Validator();
    let envResult = v.validate(req['body'], AuthTokenSchema);

    if (envResult.errors.length > 0) {
        return next(new BadRequest("Invalid values"));
    }

    let description = req['body']['description'];
    let scope_push = req['body']['scope_push'];
    let scope_pull = req['body']['scope_pull'];

    db.one(`INSERT INTO auth_token (description, scope_push, scope_pull, project_id)
            VALUES ($1, $2, $3, $4) RETURNING token`,
        [description, scope_push, scope_pull, project_id])
    .then((r) => {
        return OK(res, "Successfully added token", { token: r.token });
    }).catch(handleDBError(next));
});

router.delete("/:token_id", pv, (req: Request, res: Response, next) => {
    let token_id = req.params['token_id'];
    let project_id = req.params['project_id'];

    db.none('DELETE FROM auth_token WHERE project_id = $1 and id = $2',
        [project_id, token_id])
        .then(() => {
            return OK(res, "Successfully deleted token");
        }).catch(handleDBError(next));
});
