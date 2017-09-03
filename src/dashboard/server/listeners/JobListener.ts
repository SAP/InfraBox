import { Subject } from "rxjs/Subject";
import { Observable } from "rxjs/Observable";

import { logger } from "../utils/logger";
import { db, pgp } from "../db";
import { NotFound } from "../utils/status";

export class JobListener {
    private subject = new Subject<any>();
    private connection = null;
    private connecting = false;

    constructor() {
        this.connect();
    }

    private connect() {
        if (this.connecting) {
            return;
        }

        this.connecting = true;

        if (this.connection) {
            this.connection.done();
            this.connection = null;
        }

        setTimeout(() => {
            this.connectImpl();
        }, 3000);
    }

    private connectImpl() {
        db.connect({ direct: true })
            .then((sco) => {
                logger.debug("JobListener: established connection");
                this.connection = sco;

                sco.client.on("notification", (msg) => {
                    const update = JSON.parse(msg.payload);

                    if (update.data.commit) {
                        update.data.commit_message = update.data.commit.message.split("\n")[0];
                    }

                    if (!update.data.pull_request || !update.data.pull_request.title) {
                        update.data.pull_request = null;
                    }

                    this.subject.next(update);
                });

                sco.client.on("end", () => {
                    logger.debug("JobListener: connection ended");
                    this.connecting = false;
                    this.connect();
                });

                return sco.none("LISTEN $1~", "job_update");
            })
            .catch((error) => {
                logger.error("JobListener:", error);
                this.connecting = false;
                this.connect();
            });
    }

    public getJobs(user_id: string, project_id: string): Observable<any> {
        return Observable.create((observer) => {
            db.one(`SELECT public FROM project WHERE id = $1`, [project_id])
                .then((result: any) => {

                if (result.public) {
                    return { cnt: '1' };
                } else {
                    // private
                    if (!user_id) {
                        throw new NotFound();
                    } else {
                        // check if collaborator
                        return db.one(
                            `SELECT count(*) as cnt FROM collaborator
                             WHERE user_id = $1 and project_id = $2`, [user_id, project_id]);
                    }
                }
            }).then((result: any) => {
                if (result.cnt !== '1') {
                    throw new NotFound();
                }

                return db.any(`
                    WITH github_builds AS (
                        --- get the last 10 builds for each branch
                        SELECT builds.id, builds.project_id, builds.commit_id, null::uuid as source_upload_id, build_number, restart_counter FROM (
                            SELECT b.id, c.id as commit_id, p.id as project_id, ROW_NUMBER() OVER(PARTITION BY p.id ORDER BY build_number DESC, restart_counter DESC) AS r, build_number, restart_counter
                            FROM build b
                            INNER JOIN project p
                                ON b.project_id = $1
                                AND p.id = $1
                                AND p.type in ('github', 'gerrit')
                            LEFT OUTER JOIN commit c
                                ON b.commit_id = c.id
                                AND c.project_id = $1
                        ) builds
                        WHERE builds.r <= 10
                    ), upload_builds AS (
                        --- get the last 10 builds
                        SELECT builds.id, builds.project_id, null::character varying as commit_id, builds.source_upload_id, build_number, restart_counter  FROM (
                            SELECT b.id, p.id as project_id, source_upload_id, ROW_NUMBER() OVER(PARTITION BY p.id ORDER BY build_number DESC, restart_counter DESC) AS r, build_number, restart_counter
                            FROM build b
                            INNER JOIN project p
                                ON p.id = $1
                                AND b.project_id = p.id
                                AND p.type = 'upload'
                        ) builds
                        WHERE builds.r <= 10
                    ), builds AS (
                        SELECT * FROM github_builds
                        UNION ALL
                        SELECT * FROM upload_builds
                    )
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
                        j.cpu as job_cpu,
                        j.memory as job_memory,
                        j.dependencies as job_dependencies,
                        j.created_at as job_created_at,
                        -- pull_request
                        pr.title as pull_request_title,
                        pr.url as pull_request_url
                        FROM builds b
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
                        ORDER BY j.created_at DESC
                `, [project_id]);
            }).then((jobs) => {
                // forward
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
                            cpu: j.job_cpu,
                            memory: j.job_memory,
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

                    observer.next({
                        type: "INSERT",
                        data: o
                    });
                }

                // listen on new incoming jobs
                this.subject.subscribe((job) => {
                    if (job.data.project.id === project_id) {
                        observer.next(job);
                        return;
                    }
                });
            }).catch((err) => {
                observer.complete();
                logger.error(err);
            });
        });
    }

    public stop() {
        if (this.connection) {
            this.connection.done();
        }
        this.connection = null;
    }
}
