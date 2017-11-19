import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { BadRequest, OK } from "../../utils/status";
import { param_validation as pv } from "../../utils/validation";
import { auth, checkProjectAccess } from "../../utils/auth";

const router = Router({ mergeParams: true });
module.exports = router;

router.post("/", pv, auth, checkProjectAccess, (req, res: Response, next) => {
    req.checkBody('username', 'Invalid username').notEmpty();
    if (req.validationErrors()) {
        return next(new BadRequest("Invalid values"));
    }

    const project_id = req.params['project_id'];
    const username = req['body']['username'];

    db.tx((t) => {
        return t.any('SELECT * FROM collaborator WHERE user_id = $1 AND project_id = $2 and owner = true', [req.user.id, project_id])
            .then((result: any[]) => {
                if (result.length !== 1) {
                    throw new BadRequest('Not allowed');
                }
                return t.any(`SELECT * FROM "user" WHERE username = $1`, [username]);
            })
            .then((users) => {
                if (users.length === 0) {
                    throw new BadRequest('user not found');
                }

                const user = users[0];
                return t.none(`INSERT INTO collaborator (project_id, user_id) VALUES($1, $2) ON CONFLICT DO NOTHING`, [project_id, user.id]);
            });
    })
    .then(() => {
        return OK(res, 'successfully added user');
    })
    .catch(handleDBError(next));
});

router.delete("/:user_id", pv, auth, checkProjectAccess, (req, res: Response, next) => {
    const user_id = req.params['user_id'];
    const project_id = req.params['project_id'];
    const owner_id = req['user'].id;

    if (req.user.id === user_id) {
        throw new BadRequest("Not allowed");
    }

    db.tx((t) => {
        return t.any('SELECT * FROM collaborator WHERE user_id = $1 AND project_id = $2 and owner = true', [owner_id, project_id])
            .then((result: any[]) => {
                if (result.length !== 1) {
                    throw new BadRequest('Not allowed');
                }
                return t.none(`DELETE FROM  collaborator WHERE user_id = $1 AND project_id = $2`, [user_id, project_id]);
            });
    })
    .then(() => {
        return OK(res, 'successfully removed user');
    })
    .catch(handleDBError(next));
});

router.get("/", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    db.any(`SELECT u.name, u.id, u.email, u.avatar_url, u.username FROM "user" u
            INNER JOIN collaborator co
                ON co.user_id = u.id
                AND co.project_id = $1`,
        [project_id])
        .then((c: any[]) => {
            res.json(c);
        }).catch(handleDBError(next));
});
