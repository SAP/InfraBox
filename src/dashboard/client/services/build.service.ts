import { Job, JobState, Badge, PullRequest } from "./job.service";
import { Logger, LogService } from "./log.service";
import { Injectable } from "@angular/core";
import { Subscription } from "rxjs/Subscription";
import { ReplaySubject } from "rxjs/ReplaySubject";
import { BehaviorSubject } from "rxjs/BehaviorSubject";
import { Observable } from "rxjs/Observable";
import { JobService } from "./job.service";
import { APIService } from "../services/api.service";
import { Commit } from "../services/commit.service";
import { Project, ProjectService } from "../services/project.service";
import { Notification } from "../services/notification.service";

import 'rxjs/add/operator/filter';

type BuildID = string;
type ProjectID = string;

export class Build {
    public id: string;
    public state: BehaviorSubject<JobState>;
    public end_date: BehaviorSubject<Date>;
    public start_date: BehaviorSubject<Date>;
    public jobs = new Array<Job>();
    public project: Project;
    public commit: Commit;
    public number: number;
    public restart_counter;
    public pull_request: PullRequest;

    constructor(project: Project, id: string) {
        this.project = project;
        this.id = id;
        this.state = new BehaviorSubject<JobState>("queued");
        this.end_date = new BehaviorSubject<Date>(null);
        this.start_date = new BehaviorSubject<Date>(null);
        this.update();
    }

    public getState(): Observable<JobState> {
        return this.state;
    }

    public getStateValue(): JobState {
        return this.state.getValue();
    }

    public addJob(j: Job) {
        this.jobs.push(j);
        this.update();

        // update build state if job is updated
        j.getState().subscribe(() => {
            this.update();
        });
    }

    public update() {
        if (this.jobs.length === 0) {
            return;
        }

        let has_queued = false;
        let has_scheduled = false;
        let has_running = false;
        let has_finished = false;
        let has_failure = false;
        let has_error = false;
        let is_running = false;
        let has_killed = false;

        for (let i = 0; i < this.jobs.length; ++i) {
            const j = this.jobs[i];

            this.pull_request = j.pull_request;

            if (i === 0) {
                this.commit = j.commit;
                this.start_date.next(j.start_date.getValue());
                this.number = j.build.build_number;
                this.restart_counter = j.build.restart_counter;
            } else {
                if (j.start_date.getValue() && this.start_date.getValue() > j.start_date.getValue()) {
                    this.start_date.next(j.start_date.getValue());
                }
            }

            if (j.getStateValue() === "queued") {
                has_queued = true;
                is_running = true;
            } else if (j.getStateValue() === "scheduled") {
                has_scheduled = true;
                is_running = true;
            } else if (j.getStateValue() === "running") {
                has_running = true;
                is_running = true;
            } else if (j.getStateValue() === "finished") {
                has_finished = true;
            } else if (j.getStateValue() === "failure") {
                has_failure = true;
            } else if (j.getStateValue() === "killed") {
                has_killed = true;
            } else if (j.getStateValue() === "error") {
                has_error = true;
            }

            if (!is_running) {
                if (!this.end_date.getValue()) {
                    this.end_date.next(j.end_date.getValue());
                }

                if (this.end_date.getValue() < j.end_date.getValue()) {
                    this.end_date.next(j.end_date.getValue());
                }
            }
        }

        if (is_running) {
            this.end_date.next(null);
        }

        if (has_running) {
            if (this.state.getValue() !== "running") {
                this.state.next("running");
            }

            return;
        }

        if (has_scheduled) {
            if (this.state.getValue() !== "running") {
                this.state.next("running");
            }

            return;
        }

        if (has_queued) {
            if (this.state.getValue() !== "queued") {
                this.state.next("running");
            }

            return;
        }

        if (has_killed) {
            if (this.state.getValue() !== "killed") {
                this.state.next("killed");
            }

            return;
        }

        if (has_error) {
            if (this.state.getValue() !== "error") {
                this.state.next("error");
            }

            return;
        }

        if (has_failure) {
            if (this.state.getValue() !== "failure") {
                this.state.next("failure");
            }

            return;
        }

        if (!is_running) {
            if (this.state.getValue() !== "finished") {
                this.state.next("finished");
            }

            return;
        }
    }
}

export class JobBadges {
    public job_name: string;
    public badges: Badge[];
}

@Injectable()
export class BuildService {
    private builds = new Map<ProjectID, Map<BuildID, Build>>();
    private subscription: Subscription;
    private subject = new ReplaySubject<Build>();
    private logger: Logger;
    private projectURL = "api/dashboard/project";

    constructor(private api: APIService,
        private jobService: JobService,
        private logService: LogService,
        private projectService: ProjectService) {
        this.logger = logService.createNamedLogger("BuildService");

        this.subscription = this.jobService.getJobs().subscribe((job: Job) => {
            this.logger.debug("Received job: ", job);
            const project_id = job.project_id;
            const build_id = job.build.id;

            if (!this.builds.has(project_id)) {
                const m = new Map<BuildID, Build>();
                this.builds.set(project_id, m);
            }

            const project = this.builds.get(project_id);
            if (project.has(build_id)) {
                const b: Build = this.builds.get(project_id).get(build_id);
                b.addJob(job);
            } else {
                // First Job for this build, let's create a new one
                this.addNewBuild(project_id, build_id, job);
            }
        });
    }

    private addNewBuild(project_id: string, build_id: string, job: Job) {
        const project = this.builds.get(project_id);
        this.projectService.getProject(project_id).subscribe((r: Project) => {
            if (project.has(build_id)) {
                const b: Build = this.builds.get(project_id).get(build_id);
                b.addJob(job);
                return;
            }

            const b = new Build(r, build_id);
            b.addJob(job);
            project.set(build_id, b);

            // Notify others
            this.subject.next(b);
        });
    }

    public getBuilds(): Observable<Build> {
        return this.subject;
    }

    public getBuildsForProject(project_id: ProjectID): Observable<Build> {
        return this.getBuilds().filter((b: Build) => {
            return b.project.id === project_id;
        });
    }

    public getBuildsForBranch(project_id: ProjectID, branch: string): Observable<Build> {
        return this.getBuildsForProject(project_id).filter((b: Build) => {
            return b.commit.branch === branch;
        });
    }

    private loadBuild(project_id: ProjectID, build_id: string) {
        this.logger.debug("Loading build " + build_id);
        const url = "/api/dashboard/project/" + project_id + "/build/" + build_id;
        this.api.get(url).subscribe((jobs: any[]) => {
            this.jobService.addJobs(project_id, jobs);
        });
    }

    public getBuild(project_id: ProjectID, build_id: string): Observable<Build> {
        if (!this.builds.has(project_id)) {
            this.loadBuild(project_id, build_id);
        } else {
            const builds = this.builds.get(project_id);

            if (!builds.has(build_id)) {
                this.loadBuild(project_id, build_id);
            }
        }

        return this.getBuildsForProject(project_id).filter((b: Build) => {
            return b.id === build_id;
        });
    }

    public getMostRecentBuildForBranch(project_id: ProjectID, branch: string): Observable<Build> {
        return Observable.create((observer) => {
            const project = this.builds.get(project_id);

            if (project) {
                const builds = new Array<Build>();
                for (const value of project.values()) {
                    builds.push(value);
                }

                builds.sort((a: Build, b: Build) => {
                    if (a.start_date.getValue() === null) {
                        return 1;
                    }

                    if (b.start_date.getValue() === null) {
                        return -1;
                    }

                    return a.start_date.getValue().getTime() - b.start_date.getValue().getTime();
                });

                observer.next(builds[0]);
            }

            observer.complete();
        });
    }

    public kill(project_id: string, build_id: string): Observable<Notification> {
        const url = this.projectURL + '/' + project_id + '/build/' + build_id + '/kill';
        return this.api.get(url);
    }

    public clearCache(build: Build): Observable<Notification> {
        const url = this.projectURL + '/' + build.project.id + '/build/' + build.id + '/cache/clear';
        return this.api.get(url);
    }

    public restart(project_id: string, build_id: string): Observable<Notification> {
        const url = this.projectURL + '/' + project_id + '/build/' + build_id + '/restart';
        return this.api.get(url);
    }

    public getBadges(project_id: string, build_id: string): Observable<JobBadges[]> {
        const url = this.projectURL + '/' + project_id + '/build/' + build_id + '/badges';
        return this.api.get(url);
    }
}
