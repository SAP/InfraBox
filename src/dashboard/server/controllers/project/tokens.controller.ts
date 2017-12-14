import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { BadRequest, OK } from "../../utils/status";
import { param_validation as pv } from "../../utils/validation";
import { Validator } from 'jsonschema';
import { auth, checkProjectAccess } from "../../utils/auth";

const jwt = require('jsonwebtoken');
const fs = require('fs');

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    db.any(`SELECT description, scope_push, scope_pull, id
            FROM "auth_token" where project_id = $1`,
        [project_id])
        .then((tokens: any[]) => {
            res.json(tokens);
        }).catch(handleDBError(next));
});

const AuthTokenSchema = {
    id: "/AuthTokenSchema",
    type: "object",
    properties: {
        description: { type: "string", minLength: 3, maxLength: 255 },
        scope_pull: { type: "boolean" },
        scope_push: { type: "boolean" },
    },
    required: ["description", "scope_pull", "scope_push"]
};

router.post("/", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    const v = new Validator();
    const envResult = v.validate(req['body'], AuthTokenSchema);

    if (envResult.errors.length > 0) {
        return next(new BadRequest("Invalid values"));
    }

    const description = req['body']['description'];
    const scope_push = req['body']['scope_push'];
    const scope_pull = req['body']['scope_pull'];

    db.one(`INSERT INTO auth_token (description, scope_push, scope_pull, project_id)
            VALUES ($1, $2, $3, $4) RETURNING id`,
        [description, scope_push, scope_pull, project_id])
    .then((r) => {
        const t = {
            id: r.id,
            scope: {
                pull: scope_pull,
                push: scope_push
            },
            project: {
                id: project_id
            },
            type: 'project'
        };

        const cert = fs.readFileSync('/var/run/secrets/infrabox.net/rsa/id_rsa');
        const token = jwt.sign(t, cert, { algorithm: 'RS256'});
        return OK(res, "Successfully added token", { token: token });
    }).catch(handleDBError(next));
});

router.delete("/:token_id", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const token_id = req.params['token_id'];
    const project_id = req.params['project_id'];

    db.none('DELETE FROM auth_token WHERE project_id = $1 and id = $2',
        [project_id, token_id])
        .then(() => {
            return OK(res, "Successfully deleted token");
        }).catch(handleDBError(next));
});
