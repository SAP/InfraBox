import { Component, OnDestroy, OnInit } from "@angular/core";
import { ActivatedRoute } from "@angular/router";

import { Subscription } from "rxjs/Subscription";

import { BuildService, Build, JobBadges } from "../../services/build.service";
import { LoginService } from "../../services/login.service";
import { Job, JobState, JobService, States, Badge } from "../../services/job.service";
import { ProjectService, Project } from "../../services/project.service";

import * as _ from "lodash";

@Component({
    selector: "project-detail",
    templateUrl: "./detail.component.html",
})
export class ProjectDetailComponent implements OnInit, OnDestroy {
    private project: Project;
    private jobs_running = 0;
    private all_builds: Build[];
    private builds: Build[];
    private subs: Subscription[];
    private all_states: JobState[];
    private input_search: string;
    private input_states: Map<JobState, boolean>;
    private project_id: string;
    private badges: JobBadges[];
    private latestBuild: Build = null;

    constructor(private projectService: ProjectService,
        private loginService: LoginService,
        private jobService: JobService,
        private buildService: BuildService,
        private route: ActivatedRoute) {
        this.all_states = States;
    }

    private init(): void {
        this.unsubscribe();
        this.project = null;
        this.builds = new Array<Build>();
        this.all_builds = new Array<Build>();
        this.subs = new Array<Subscription>();
        this.jobs_running = 0;
        this.input_search = "";
        this.input_states = new Map<JobState, boolean>();
        this.latestBuild = null;
        this.badges = new Array<JobBadges>();

        for (const s of this.all_states) {
            this.input_states.set(s, true);
        }
    }

    public ngOnInit(): void {
        this.init();

        this.route.params.subscribe((params) => {
            this.init();

            this.project_id = params["project_id"];

            this.subs.push(this.projectService.getProject(this.project_id).subscribe((r: Project) => {
                this.project = r;
            }));

            this.subs.push(this.jobService.getJobs().filter((j: Job) => {
                return j.project_id === this.project_id;
            }).subscribe((j: Job) => {
                const sv = j.getStateValue();
                switch (sv) {
                    case "scheduled":
                    case "running":
                    case "queued": {
                        this.jobs_running += 1;

                        this.subs.push(j.getState().subscribe((js: JobState) => {
                            if (js !== "queued" && js !== "scheduled" && js !== "running") {
                                this.jobs_running -= 1;
                            }
                        }));
                    }
                    default:
                }
            }));

            this.subs.push(this.buildService.getBuildsForProject(this.project_id)
                           .subscribe((b: Build) => {
                this.all_builds.unshift(b);
                this.all_builds = _.orderBy(this.all_builds, ["number", "restart_counter"], ["desc", "desc"]);

                if (this.checkFilter(b)) {
                    this.builds.unshift(b);
                    this.builds = _.orderBy(this.builds, ["number", "restart_rounter"], ["desc", "desc"]);
                }

                if (b.getStateValue() === 'finished') {
                    this.latestBuild = b;
                    this.subs.push(this.buildService.getBadges(this.project_id, b.id)
                                   .subscribe((badges: JobBadges[]) => {
                        this.badges = badges;
                    }));
                }

                if (b.getStateValue() === 'running') {
                    this.subs.push(b.getState().subscribe((state: JobState) => {
                        if (state === 'finished') {
                            this.latestBuild = b;
                            this.subs.push(this.buildService.getBadges(this.project_id, b.id)
                                           .subscribe((badges: JobBadges[]) => {
                                this.badges = badges;
                            }));
                        }
                    }));
                }
            }));
        });
    }

    private checkFilter(b: Build): boolean {
        if (this.input_search && this.input_search !== "") {
            if (!b.commit.message.includes(this.input_search)) {
                return false;
            }
        }

        const state = b.getStateValue();
        if (!this.input_states.get(state)) {
            return false;
        }

        return true;
    }

    public change(s: JobState) {
        const state = this.input_states.get(s);
        this.input_states.set(s, !state);
    }

    public search() {
        this.builds = new Array<Build>();

        for (const b of this.all_builds) {
            if (this.checkFilter(b)) {
                this.builds.push(b);
            }
        }
    }

    public getVisibility(s: JobState) {
        const v = this.input_states.get(s);
        return v;
    }

    private unsubscribe() {
        if (!this.subs) {
            return;
        }

        for (const s of this.subs) {
            s.unsubscribe();
        }

        this.subs = null;
    }

    public ngOnDestroy() {
        this.unsubscribe();
    }
}
