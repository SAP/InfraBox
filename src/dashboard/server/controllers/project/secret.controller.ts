import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { OK, BadRequest } from "../../utils/status";
import { Validator } from 'jsonschema';
import { param_validation as pv } from "../../utils/validation";
import { auth, checkProjectAccess } from "../../utils/auth";

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    db.any(`
        SELECT name, id FROM secret
        WHERE project_id = $1`
        , [project_id]
    ).then((vars: any[]) => {
        res.json(vars);
    }).catch(handleDBError(next));
});

const SecretSchema = {
    id: "/SecretSchema",
    type: "object",
    properties: {
        name: { type: "string" },
        value: { type: "string" },
    },
    required: ["name", "value"]
};

router.post("/", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    const v = new Validator();
    const secretResult = v.validate(req['body'], SecretSchema);

    if (secretResult.errors.length > 0) {
        return next(new BadRequest("Invalid values"));
    }

    const name = req['body']['name'];
    const value = req['body']['value'];

    db.one(`SELECT COUNT(*) as cnt FROM secret WHERE project_id = $1`,
        [project_id]
    ).then((data: any) => {
        if (data.cnt > 50) {
            throw new BadRequest("too many secrets");
        }

        return db.none(`INSERT INTO secret (project_id, name, value) VALUES($1, $2, $3)`,
            [project_id, name, value]);
    }).then(() => {
        return OK(res, 'successfully added secret variable');
    })
    .catch(handleDBError(next));
});

router.delete("/:secret_id", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const secret_id = req.params['secret_id'];

    db.none(`DELETE FROM secret WHERE project_id = $1 and id = $2`,
        [project_id, secret_id]
    ).then(() => {
        return OK(res, 'successfully deleted secret');
    })
    .catch(handleDBError(next));
});
