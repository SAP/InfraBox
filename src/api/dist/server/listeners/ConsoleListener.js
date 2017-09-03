"use strict";
const ReplaySubject_1 = require("rxjs/ReplaySubject");
const logger_1 = require("../utils/logger");
const db_1 = require("../db");
class ConsoleOutput {
    constructor() {
        this.subject = new ReplaySubject_1.ReplaySubject();
    }
}
exports.ConsoleOutput = ConsoleOutput;
class ConsoleListener {
    constructor() {
        this.output = new Map();
        this.connection = null;
        this.connecting = false;
        this.connect();
    }
    connect() {
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
    connectImpl() {
        db_1.db.connect({ direct: true })
            .then((sco) => {
            logger_1.logger.debug("ConsoleListener: established connection");
            this.connection = sco;
            sco.client.on("notification", (msg) => {
                const update = JSON.parse(msg.payload);
                logger_1.logger.debug("Received console update", update);
                this.handleNotification(update);
            });
            sco.client.on("end", () => {
                logger_1.logger.debug("ConsoleListener: connection ended");
                this.connecting = false;
                this.connect();
            });
            return sco.none("LISTEN $1~", "console_update");
        })
            .catch((error) => {
            logger_1.logger.error("ConsoleListener:", error);
            this.connecting = false;
            this.connect();
        });
    }
    handleNotification(event) {
        const job_id = event.job_id;
        if (!this.output.has(job_id)) {
            // we are not interested in this output
            return;
        }
        const output = this.output.get(job_id);
        db_1.db.any("SELECT output FROM console WHERE id = $1;", [event.id])
            .then((result) => {
            if (result.length > 0) {
                output.subject.next(result[0].output);
            }
        });
    }
    getOutput(job_id, user_id) {
        logger_1.logger.debug("getOutput:", job_id, user_id);
        if (this.output.has(job_id)) {
            return this.output.get(job_id).subject;
        }
        const out = new ConsoleOutput();
        db_1.db.any(`SELECT j.* FROM job j
                INNER JOIN collaborator co
                    ON co.project_id = j.project_id
                    AND co.user_id = $1
                    AND j.id = $2
         `, [user_id, job_id])
            .then((jobs) => {
            if (jobs.length === 0) {
                out.subject.complete();
                return;
            }
            const job = jobs[0];
            if (job.state === "finished" || job.state === "failure" || job.state === "error" || job.state === "killed" || job.state === "skipped") {
                out.subject.next(job.console);
                out.subject.complete();
            }
            else {
                return db_1.db.any("SELECT output FROM console WHERE job_id = $1 ORDER BY date;", [job_id]).then((result) => {
                    // a parallel request might have added the job_id
                    // already so we have to check it in forward the values
                    if (this.output.has(job_id)) {
                        this.output.get(job_id).subject.subscribe(out.subject);
                    }
                    else {
                        this.output.set(job_id, out);
                        for (const r of result) {
                            out.subject.next(r.output);
                        }
                    }
                });
            }
        }).catch((err) => {
            logger_1.logger.error(err);
        });
        return out.subject;
    }
    stop() {
        if (this.connection) {
            this.connection.done();
        }
        this.connection = null;
    }
}
exports.ConsoleListener = ConsoleListener;
