import { ReplaySubject } from "rxjs/ReplaySubject";
import { Observable } from "rxjs/Observable";

import { logger } from "../utils/logger";
import { db } from "../db";
import { NotFound } from "../utils/status";

import prom = require('prom-client');

const CONSOLE_NOTIFICATIONS = new prom.Counter({
    name: "infrabox_dashboard_console_update_notifications",
    help: "Number of console update notifictions"
});

const CACHED_CONSOLE = new prom.Gauge({
    name: "infrabox_dashboard_cached_console_outputs",
    help: "Number of cached console outputs"
});

class ConsoleOutputCache {
    private output = new Map<string, ReplaySubject<string>>();

    public has(job_id: string): boolean {
        return this.output.has(job_id);
    }

    public get(job_id: string) {
        return this.output.get(job_id);
    }

    public set(job_id: string, subject: ReplaySubject<string>) {
        CACHED_CONSOLE.inc();
        return this.output.set(job_id, subject);
    }
}

export class ConsoleListener {
    private cache = new ConsoleOutputCache();

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
                logger.debug("ConsoleListener: established connection");
                this.connection = sco;

                sco.client.on("notification", (msg) => {
                    const update = JSON.parse(msg.payload);
                    logger.debug("Received console update", update);
                    CONSOLE_NOTIFICATIONS.inc();
                    this.handleNotification(update);
                });

                sco.client.on("end", () => {
                    logger.debug("ConsoleListener: connection ended");
                    this.connecting = false;
                    this.connect();
                });

                return sco.none("LISTEN $1~", "console_update");
            })
            .catch((error) => {
                logger.error("ConsoleListener:", error);
                this.connecting = false;
                this.connect();
            });
    }

    public handleNotification(event) {
        const job_id: string = event.job_id;

        if (!this.cache.has(job_id)) {
            // we are not interested in this output
            return;
        }

        const subject = this.cache.get(job_id);
        db.any("SELECT output FROM console WHERE id = $1;", [event.id])
        .then((result: any[]) => {
            if (result.length > 0) {
                subject.next(result[0].output);
            }
        });
    }

    public getOutput(job_id: string, user_id: string): Observable<string> {
        logger.debug("getOutput:", job_id, user_id);
        if (this.cache.has(job_id)) {
            return this.cache.get(job_id);
        }

        const out = new ReplaySubject<string>();

        db.any(`SELECT j.*, p.public
                FROM project p
                INNER JOIN job j
                    ON j.project_id = p.id
                    AND j.id = $1`, [job_id])
            .then((result: any[]) => {

            if (result.length !== 1) {
                throw new NotFound();
            }

            if (result[0].public) {
                return result;
            } else {
                if (!user_id) {
                    throw new NotFound();
                } else {
                    return db.any(`SELECT j.* FROM job j
                            INNER JOIN collaborator co
                                ON co.project_id = j.project_id
                                AND co.user_id = $1
                                AND j.id = $2
                     `, [user_id, job_id]);
                }
            }
        })
       .then((jobs: any[]) => {
            if (jobs.length === 0) {
                out.complete();
                return;
            }

            const job = jobs[0];

            if (job.state === "finished" || job.state === "failure" || job.state === "error" || job.state === "killed" || job.state === "skipped") {
                out.next(job.console);
                out.complete();
            } else {
                return db.any("SELECT output FROM console WHERE job_id = $1 ORDER BY date;", [job_id]).then((result) => {
                    // a parallel request might have added the job_id
                    // already so we have to check it and forward the values
                    if (this.cache.has(job_id)) {
                        this.cache.get(job_id).subscribe(out);
                    } else {
                        this.cache.set(job_id, out);
                        for (const r of result) {
                            out.next(r.output);
                        }
                    }
                });
            }
        }).catch((err) => {
            logger.error(err);
            out.complete();
        });

        return out;
    }

    public stop() {
        if (this.connection) {
            this.connection.done();
        }
        this.connection = null;
    }
}
