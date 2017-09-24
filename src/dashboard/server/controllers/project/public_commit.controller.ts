import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { param_validation as pv } from "../../utils/validation";

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/:commit_id", pv, (req: Request, res: Response, next) => {
    const commit_id = req.params['commit_id'];
    const project_id = req.params['project_id'];

    db.tx((t) => {
        // Select the commit
        return t.one(`SELECT c.* FROM commit c
               WHERE c.id = $2
               AND c.project_id = $1`,
            [project_id, commit_id]);
    })
    .then((commit: any) => {
        res.send(commit);
    }).catch(handleDBError(next));
});
