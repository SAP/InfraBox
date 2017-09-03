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
        return t.batch([
            // Select the commit
            t.one(`SELECT c.* FROM commit c
                   WHERE c.id = $2
                   AND c.project_id = $1`,
                [project_id, commit_id]),

            // Select all the modified files
            t.any(`SELECT modification, filename FROM commit_file
                   WHERE project_id = $1
                   AND commit_id = $2`, [project_id, commit_id])
        ]);
    })
    .then((data: any[]) => {
        const commit = data[0];
        commit['modified'] = [];
        commit['removed'] = [];
        commit['added'] = [];

        const files = data[1];

        for (const f of files) {
            commit[f.modification].push(f.filename);
        }

        res.send(commit);
    }).catch(handleDBError(next));
});
