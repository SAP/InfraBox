import { Injectable } from "@angular/core";
import { Observable } from "rxjs/Observable";
import { Subject } from "rxjs/Subject";
import { BehaviorSubject } from "rxjs/BehaviorSubject";
import { ReplaySubject } from "rxjs/ReplaySubject";

import { EventService } from "../services/event.service";
import { Commit, CommitService } from "../services/commit.service";
import { Logger, LogService } from "../services/log.service";
import { NotificationService, Notification  } from "../services/notification.service";
import { APIService } from "../services/api.service";

export type JobState = "queued" | "scheduled" | "running" | "finished" | "failure" | "error" | "killed" | "skipped";

export let States: JobState[] = ["queued", "scheduled", "running", "finished", "failure", "error", "killed", "skipped"];

class BuildInfo {
    constructor(public id: string,
    public build_number: number,
    public restart_counter: number) {}
}

export class SourceUpload {
    public filename: string;
    public filesize: number;
}

export class Tab {
    constructor(public name: string, public data: string, public type: string) {}
}

export class Badge {
    constructor(public subject: string, public status: string, public color: string) {}
}

export class JobStatValues {
    constructor(public date: number, mem: number, cpu: number) {}
}

export class EnvironmentVariable {
    constructor(public name: string, public value: string, public ref: boolean) {}
}

export class PullRequest {
    constructor(public title: string) {}
}

export class Dependency {
    public job: string;
    public "job-id": string;
    public on: string;
}

export class Job {
    private state: BehaviorSubject<JobState>;
    public end_date: BehaviorSubject<Date>;
    public start_date: BehaviorSubject<Date>;
    public subject = new Subject<Job>();
    public id: string;
    public created_at: Date;
    public build: BuildInfo;
    public project_id: string;
    public commit: Commit;
    public name: string;
    public cpu: number;
    public memory: number;
    public dependencies = new Array<Dependency>();
    public source_upload: SourceUpload;
    public pull_request: PullRequest;

    constructor(o: any, commit: Commit) {
        this.id = o.job.id;
        this.state = new BehaviorSubject<JobState>(o.job.state);

        this.created_at = new Date(o.job.created_at);

        if (o.job.start_date) {
            this.start_date = new BehaviorSubject<Date>(new Date(o.job.start_date));
        } else {
            this.start_date = new BehaviorSubject<Date>(null);
        }

        if (o.job.end_date) {
            this.end_date = new BehaviorSubject<Date>(new Date(o.job.end_date));
        } else {
            this.end_date = new BehaviorSubject<Date>(null);
        }

        this.build = new BuildInfo(o.build.id, o.build.build_number, o.build.restart_counter);

        this.project_id = o.project.id;
        this.name = o.job.name;
        this.cpu = o.job.cpu;
        this.memory = o.job.memory;
        this.commit = commit;
        if (o.job.dependencies) {
            this.dependencies = o.job.dependencies;
        }

        if (o.pull_request) {
            this.pull_request = o.pull_request;
        }

        if (o.source_upload) {
            this.source_upload = o.source_upload;
        }
    }

    public getState(): Observable<JobState> {
        return this.state;
    }

    public getStateValue(): JobState {
        return this.state.getValue();
    }

    public update(o: any) {
        console.assert(o.id === this.id, "Wrong object");
        this.state.next(o.state);
        this.subject.next(this);
        if (o.end_date) {
            this.end_date.next(new Date(o.end_date));
        }

        if (o.start_date && this.start_date.getValue() === null) {
            this.start_date.next(new Date(o.start_date));
        }
    }
}

export class JobEvent {
    public type: string;
    public data: any;
}

@Injectable()
export class JobService {
    private jobs: Map<string, Job> = new Map<string, Job>();
    private subject = new ReplaySubject<Job>();
    private logger: Logger;
    private listeningTo = new Set<string>();

    constructor(private eventService: EventService,
                private logService: LogService,
                private commitService: CommitService,
                private notificationService: NotificationService,
                private api: APIService) {
        this.logger = logService.createNamedLogger("JobService");
    }

    public startListening(project_id: string) {
        if (this.listeningTo.has(project_id)) {
            return;
        }

        this.listeningTo.add(project_id);

        this.eventService
            .listen("jobs", project_id)
            .subscribe((event: JobEvent) => {
                if (event.data.project.id !== project_id) {
                    return;
                }

                this.logger.debug("received event", event);

                if (event.type === "UPDATE") {
                    if (this.jobs.has(event.data.job.id)) {
                        const j: Job = this.jobs.get(event.data.job.id);
                        j.update(event.data.job);
                        return;
                    } else {
                        // let's treat it as INSERT
                        event.type = "INSERT";
                    }
                }

                if (event.type === "INSERT") {
                    this.handleJobInsert(event.data);
                } else if (event.type === "ALL") {
                    for (const j of event.data) {
                        this.handleJobInsert(j);
                    }
                } else {
                    this.logger.error("Unknown event type", event);
                }
            });
    }

    private handleJobInsert(job_data: any) {
        if (this.jobs.has(job_data.job.id)) {
            return;
        }

        let commit = null;

        if (job_data.commit) {
            commit = this.commitService.getOrCreateCommitFromEvent(job_data);
        }
        const job = new Job(job_data, commit);
        this.jobs.set(job_data.job.id, job);
        this.subject.next(job);
    }

    public getJobs(): Observable<Job> {
        return this.subject;
    }

    public getJobsForBuild(build_id: string): Observable<Job> {
        return this.getJobs().filter((j: Job) => {
            return j.build.id === build_id;
        });
    }

    public clearCache(job: Job): Observable<Notification> {
        const url = '/api/dashboard/project/' + job.project_id + '/job/' + job.id + '/cache/clear';
        return this.api.get(url);
    }

    public kill(job: Job): Observable<Notification> {
        const url = '/api/dashboard/project/' + job.project_id + '/job/' + job.id + '/kill';
        return this.api.get(url);
    }

    public restart(job: Job): Observable<Notification> {
        const url = '/api/dashboard/project/' + job.project_id + '/job/' + job.id + '/restart';
        return this.api.get(url);
    }

    public getJob(id: string): Observable<Job> {
        return this.getJobs().filter((j: Job) => {
            return j.id === id;
        });
    }

    public addJobs(project_id: string, jobs: any[]) {
        this.startListening(project_id);
        for (const j of jobs) {
            this.handleJobInsert(j);
        }
    }

    public getTabs(project_id: string, job_id: string): Observable<Tab[]> {
        const url = '/api/dashboard/project/' + project_id + '/job/' + job_id + '/tabs';
        return this.api.get(url);
    }

    public getBadges(project_id: string, job_id: string): Observable<Badge[]> {
        const url = '/api/dashboard/project/' + project_id + '/job/' + job_id + '/badges';
        return this.api.get(url);
    }

    public getDownloads(project_id: string, job_id: string): Observable<any> {
        const url = '/api/dashboard/project/' + project_id + '/job/' + job_id + '/downloads';
        return this.api.get(url);
    }

    public getDownload(project_id: string, job_id: string, file_id: string, file_name: string) {
        const url = '/api/dashboard/project/' + project_id + '/job/' + job_id + '/downloads/' + file_id;
        return this.api.download(url, file_name);
    }

    public downloadConsoleOutput(project_id: string, job_id: string) {
        const url = '/api/dashboard/project/' + project_id + '/job/' + job_id + '/console';
        const file_name = job_id + "-console-output.txt";
        return this.api.download(url, file_name);
    }

    public getStats(project_id: string, job_id: string): Observable<any> {
        const url = '/api/dashboard/project/' + project_id + '/job/' + job_id + '/stats';
        return this.api.get(url);
    }

    public getEnv(project_id: string, job_id: string): Observable<EnvironmentVariable[]> {
        const url = '/api/dashboard/project/' + project_id + '/job/' + job_id + '/env';
        return this.api.get(url);
    }
}
