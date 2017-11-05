import { Router } from "express";
import { Request, Response } from "express";
import { auth } from "../../utils/auth";
import { OK, BadRequest } from "../../utils/status";
import { db, handleDBError } from "../../db";
import { getRepos, createDeployKey, createHook } from "../../utils/github";

const router = Router();
router.use(auth);

module.exports = router;

router.get("/repos", (req: Request, res: Response, next) => {
    const user_id = req['user'].id;

    let repos = null;

    db.one(`
        SELECT github_api_token FROM "user" WHERE id = $1
    `, [user_id])
    .then((user: any) => {
        return getRepos(user.github_api_token);
    }).then((r: any[]) => {
        repos = r;
        return db.task((t) => {
            const queries = [];
            for (const repo of repos) {
                const q = db.any("SELECT github_id FROM repository WHERE github_id = $1", [repo.id]);
                queries.push(q);
            }
            return t.batch(queries);
        });
    }).then((result: any[]) => {
        for (const match of result) {
            if (match.length > 0) {
                for (const repo of repos) {
                    if (repo.id === match[0].github_id) {
                        repo.connected = true;
                        break;
                    }
                }
            }
        }

        res.json(repos);
    }).catch(handleDBError(next));
});
