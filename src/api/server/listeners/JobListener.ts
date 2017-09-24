import { Subject } from "rxjs/Subject";
import { Observable } from "rxjs/Observable";

import 'rxjs/add/operator/filter';

import { logger } from "../utils/logger";
import { db, pgp } from "../db";

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

    public getJobs(project_id: string): Observable<any> {
        return this.subject.filter((job) => {
            return job.data.project.id === project_id;
        });
    }

    public stop() {
        if (this.connection) {
            this.connection.done();
        }
        this.connection = null;
    }
}
