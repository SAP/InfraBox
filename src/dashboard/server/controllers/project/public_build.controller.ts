import { Request, Response } from "express";
import { Router } from "express";
import { restart_build } from './restart_build';
import { db, handleDBError } from '../../db';
import { BadRequest, OK } from "../../utils/status";
import { deleteCache } from "../../utils/gcs";
import { param_validation as pv } from "../../utils/validation";

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/:build_id/badges", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const build_id = req.params['build_id'];

    db.any(`SELECT j.name, subject, status, color
            FROM job_badge jb
            JOIN job j
                ON jb.job_id = j.id
                AND j.project_id = $1
                AND jb.project_id = $1
                AND j.build_id = $2`,
           [project_id, build_id])
        .then((badges: any[]) => {
            const result = [];

            for (const b of badges) {
                let found = false;
                for (const r of result) {
                   if (r.job_name === b.name) {
                       r.badges.push({
                            color: b.color,
                            subject: b.subject,
                            status: b.status
                       });
                       found = true;
                       break;
                   }
                }

                if (!found) {
                    result.push({
                        job_name: b.name,
                        badges: [{
                            color: b.color,
                            subject: b.subject,
                            status: b.status
                        }]
                    });
                }
            }

            res.json(result);
        }).catch(handleDBError(next));
});

router.get("/:build_id", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const build_id = req.params['build_id'];

    db.any(`
        SELECT
            -- build
            b.id as build_id,
            b.build_number as build_number,
            b.restart_counter as build_restart_counter,
            -- project
            p.id as project_id,
            p.name as project_name,
            p.type as project,
            -- commit
            c.id as commit_id,
            c.message as commit_message,
            c.author_name as commit_author_name,
            c.author_email as commit_author_email,
            c.author_username as commit_author_email,
            c.committer_name as commit_committer_name,
            c.committer_email as commit_committer_email,
            c.committer_username as commit_committer_username,
            u.avatar_url as commit_committer_avatar_url,
            c.url as commit_url,
            c.branch as commit_branch,
            c.tag as commit_tag,
            -- source_upload
            su.filename as source_upload_filename,
            su.filesize as source_upload_filesize,
            -- job
            j.id as job_id,
            j.state as job_state,
            j.start_date as job_start_date,
            j.type as job_type,
            j.end_date as job_end_date,
            j.name as job_name,
            j.memory as job_memory,
            j.cpu as job_cpu,
            j.dependencies as job_dependencies,
            j.created_at as job_created_at,
            -- pull_request
            pr.title as pull_request_title
        FROM build b
        INNER JOIN job j
        ON b.id = j.build_id
        INNER JOIN project p
        ON j.project_id = p.id
        LEFT OUTER JOIN commit c
        ON b.commit_id = c.id
        LEFT OUTER JOIN source_upload su
        ON b.source_upload_id = su.id
        LEFT OUTER JOIN "user" u
        ON c.committer_username = u.username
        LEFT OUTER JOIN pull_request pr
        ON c.pull_request_id = pr.id
        WHERE   p.id = $1
            AND b.id = $2
        `,
           [project_id, build_id])
        .then((jobs: any[]) => {
            const result = [];
            for (let i = jobs.length - 1; i >= 0; --i) {
                const j = jobs[i];

                const o = {
                    build: {
                        id: j.build_id,
                        build_number: j.build_number,
                        restart_counter: j.build_restart_counter
                    },
                    project: {
                        id: j.project_id,
                        name: j.project_name,
                        type: j.project_type
                    },
                    commit: null,
                    pull_request: null,
                    source_upload: null,
                    job: {
                        id: j.job_id,
                        state: j.job_state,
                        start_date: j.job_start_date,
                        end_date: j.job_end_date,
                        name: j.job_name,
                        memory: j.job_memory,
                        cpu: j.job_cpu,
                        dependencies: j.job_dependencies,
                        created_at: j.job_created_at
                    }
                };

                if (j.pull_request_title) {
                    const pr = {
                        title: j.pull_request_title,
                        url: j.pull_request_url
                    };

                    o.pull_request = pr;
                }


                if (j.commit_id) {
                    const commit = {
                        id: j.commit_id,
                        message: j.commit_message,
                        author_name: j.commit_author_name,
                        author_email: j.commit_author_email,
                        author_username: j.commit_author_email,
                        committer_name: j.commit_committer_name,
                        committer_email: j.commit_committer_email,
                        committer_username: j.commit_committer_username,
                        committer_avatar_url: j.commit_committer_avatar_url,
                        url: j.commit_url,
                        branch: j.commit_branch,
                        tag: j.commit_tag
                    };

                    o.commit = commit;
                }

                if (j.source_upload_filename) {
                    const up = {
                        filename: j.source_upload_filename,
                        filesize: j.source_upload_filesize
                    };

                    o.source_upload = up;
                }

                result.push(o);
            }

            res.json(result);
        }).catch(handleDBError(next));
});
