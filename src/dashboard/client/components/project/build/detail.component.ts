import { Component, OnDestroy, OnInit } from "@angular/core";
import { ActivatedRoute, Router } from "@angular/router";
import { Subscription } from "rxjs/Subscription";
import { Observable } from "rxjs/Observable";

import { Logger, LogService } from "../../../services/log.service";
import { Commit, CommitService } from "../../../services/commit.service";
import { ProjectService, Project } from "../../../services/project.service";
import { Build, BuildService, JobBadges } from "../../../services/build.service";
import { Job, Badge, JobService, JobState } from "../../../services/job.service";
import { Notification, NotificationService } from "../../../services/notification.service";
import { LoginService } from "../../../services/login.service";
import { GanttChart } from "../../../utils/GanttChart";

@Component({
    selector: "build-detail",
    templateUrl: "./detail.component.html",
    host: {
        '(window:resize)': 'onResize($event)'
    }
})
export class BuildDetailComponent implements OnInit, OnDestroy {
    private subs = new Array<Subscription>();
    private project: Project;
    private build: Build;
    private jobs: Job[];
    private commit: Commit;
    private branchBuilds: Build[];
    private chart: GanttChart;
    private badges: JobBadges[];
    private isDrawing = false;
    private project_id: string;
    private build_id: string;
    private logger: Logger;

    constructor(
        private route: ActivatedRoute,
        private commitService: CommitService,
        private projectService: ProjectService,
        private buildService: BuildService,
        private notificationService: NotificationService,
        private jobService: JobService,
        private loginService: LoginService,
        private logService: LogService,
        private router: Router) {
        this.chart = new GanttChart(router);
        this.logger = logService.createNamedLogger("BuildDetailComponent");
    }

    public onResize(event) {
        this.redraw();
    }

    private getData() {
        this.logger.debug("loading project");
        return this.projectService.getProject(this.project_id)
        .flatMap((p: Project) => {
            this.project = p;
            this.logger.debug("loading badges");
            return this.buildService.getBadges(this.project_id, this.build_id);
        }).flatMap((badges: JobBadges[]) => {
            this.badges = badges;
            this.logger.debug("loading build");
            return this.buildService.getBuild(this.project_id, this.build_id);
        }).flatMap((b: Build) => {
            this.build = b;
            if (this.project.type === 'github' || this.project.type === 'gerrit') {
                this.logger.debug("loading commit");
                return this.commitService.getCommit(this.project_id, this.build.commit.id);
            } else {
                return Observable.from([null]);
            }
        }).flatMap((c: Commit) => {
            this.commit = c;

            if (c) {
                this.logger.debug("loading builds for branch");
                return this.buildService.getBuildsForBranch(this.project_id, c.branch);
            } else {
                return Observable.from([null]);
            }
        }).flatMap((build: Build) => {
            this.branchBuilds.unshift(build);
            return Observable.from([null]);
        });
    }

    private getJobs() {
        return this.jobService.getJobsForBuild(this.build_id)
        .flatMap((j: Job) => {
            this.jobs.push(j);
            this.jobs.sort((left: Job, right: Job) => {
                if (left.created_at < right.created_at) {
                    return -1;
                }

                if (left.created_at > right.created_at) {
                    return 1;
                }

                return 0;
            });

            const state = j.getStateValue() as string;
            if (state !== 'failure' ||
                state !== 'error' ||
                state !== 'finished' ||
                state !== 'killed') {
                this.subs.push(j.getState().subscribe((s: JobState) => {
                    this.chart.updateJob(j);
                }));
            }

            this.redraw();
            return Observable.from([null]);
       });
    }

    public ngOnInit(): void {
        this.subs.push(this.route.params.flatMap((params) => {
            this.init();

            this.project_id = params["project_id"];
            this.build_id = params["build_id"];

            return Observable.forkJoin(
                this.getData(),
                this.getJobs()
            );
        }).subscribe());
    }

    public redraw() {
        if (this.isDrawing) {
            return;
        }

        this.isDrawing = true;

        if (!document.getElementById("holder")) {
            setTimeout(() => {
                this.redraw();
            }, 100);
        }

        setTimeout(() => {
            const r = document.getElementById("holder");

            if (!r) {
                this.isDrawing = false;
                this.redraw();
                return;
            }

            this.chart.setJobs(this.jobs);
            this.chart.draw();
            this.isDrawing = false;
        }, 250);
    }

    public restart(build: Build) {
        this.subs.push(this.buildService.restart(this.project.id, build.id)
            .subscribe((n: Notification) => {
            const new_build_id = n.data.build.id;
            this.router.navigate(["/dashboard", "project", this.project.id, "build", new_build_id]);
            this.notificationService.notify(n);
        }));
    }

    public kill(build: Build) {
        this.subs.push(this.buildService.kill(this.project.id, build.id)
            .subscribe((n: Notification) => {
            this.notificationService.notify(n);
        }));
    }

    public clearCache(build: Build) {
        this.subs.push(this.buildService.clearCache(build).subscribe((n: Notification) => {
            this.notificationService.notify(n);
        }));
    }

    public ngOnDestroy() {
        this.unsubscribe();
    }

    private init() {
        this.unsubscribe();
        this.project = null;
        this.build = null;
        this.jobs = new Array<Job>();
        this.commit = null;
        this.branchBuilds = new Array<Build>();
        this.badges = new Array<JobBadges>();
        this.project_id = null;
        this.build_id = null;
    }

    private unsubscribe() {
        for (const s of this.subs) {
            s.unsubscribe();
        }

        this.subs = new Array<Subscription>();
    }
}
