import { ReplaySubject } from "rxjs/ReplaySubject";
import { Observable } from "rxjs/Observable";

import { logger } from "../utils/logger";
import { db } from "../db";

export class ConsoleOutput {
    public subject: ReplaySubject<string> = new ReplaySubject<string>();
    public constructor(public project_id: string) {}
}

export class ConsoleListener {
    private output = new Map<string, ConsoleOutput>();
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

        if (!this.output.has(job_id)) {
            // we are not interested in this output
            return;
        }

        const output = this.output.get(job_id);

        db.any("SELECT output FROM console WHERE id = $1;", [event.id])
        .then((result: any[]) => {
            if (result.length > 0) {
                output.subject.next(result[0].output);
            }
        });
    }

    public getOutput(job_id: string, project_id: string): Observable<string> {
        logger.debug("getOutput:", job_id, project_id);
        if (this.output.has(job_id)) {
            const c = this.output.get(job_id);

            if (c.project_id === project_id) {
                return c.subject;
            }
        }

        const out = new ConsoleOutput(project_id);

        db.any(`SELECT *
                FROM job
                WHERE project_id = $1
                AND id = $2
         `, [project_id, job_id])
        .then((jobs: any[]) => {
            if (jobs.length === 0) {
                out.subject.complete();
                return;
            }

            const job = jobs[0];

            if (job.state === "finished" || job.state === "failure" || job.state === "error" || job.state === "killed" || job.state === "skipped") {
                out.subject.next(job.console);
                out.subject.complete();
            } else {
                return db.any("SELECT output FROM console WHERE job_id = $1 ORDER BY date;", [job_id]).then((result) => {
                    // a parallel request might have added the job_id
                    // already so we have to check it in forward the values
                    if (this.output.has(job_id)) {
                        this.output.get(job_id).subject.subscribe(out.subject);
                    } else {
                        this.output.set(job_id, out);
                        for (const r of result) {
                            out.subject.next(r.output);
                        }
                    }
                });
            }
        }).catch((err) => {
            logger.error(err);
        });

        return out.subject;
    }

    public stop() {
        if (this.connection) {
            this.connection.done();
        }
        this.connection = null;
    }
}
