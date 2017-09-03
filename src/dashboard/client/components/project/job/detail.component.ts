import { Component, OnInit, OnDestroy } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { Subscription } from "rxjs/Subscription";

import { ProjectService, Project } from "../../../services/project.service";
import { Build, BuildService } from "../../../services/build.service";
import { LoginService } from "../../../services/login.service";
import { Job, Tab, Badge, JobService, JobState, EnvironmentVariable } from "../../../services/job.service";
import { Logger, LogService } from "../../../services/log.service";

import 'rxjs/add/observable/forkJoin';

@Component({
    selector: "job-detail",
    templateUrl: "./detail.component.html"
})
export class JobDetailComponent implements OnInit, OnDestroy {
    private sub: Subscription;
    private job: Job;
    private project: Project;
    private build: Build;
    private tabs: Tab[];
    private badges: Badge[];
    private downloads: any;
    private environment: EnvironmentVariable[];
    private cli_command = "";
    private ready = false;

    constructor(private jobService: JobService,
        private route: ActivatedRoute,
        private projectService: ProjectService,
        private buildService: BuildService,
        private loginService: LoginService) {}

    private init(): void {
        this.unsubscribe();
        this.tabs = new Array<Tab>();
        this.ready = false;
    }

    public ngOnInit(): void {
        this.init();
        let project_id = null;
        let build_id = null;
        let job_id = null;

        this.sub = this.route.params.flatMap((params) => {
            project_id = params["project_id"];
            build_id = params["build_id"];
            job_id = params["job_id"];
            return this.projectService.getProject(project_id);
        }).flatMap((r: Project) => {
            this.project = r;
            return this.buildService.getBuild(project_id, build_id);
        }).flatMap((b: Build) => {
            this.build = b;
            return this.jobService.getTabs(project_id, job_id);
        }).flatMap((tabs: Tab[]) => {
            this.tabs = tabs;
            return this.jobService.getJob(job_id);
        }).flatMap((j: Job) => {
            this.job = j;
            return this.jobService.getBadges(project_id, job_id);
        }).flatMap((badges: Badge[]) => {
            this.badges = badges;
            return this.jobService.getDownloads(project_id, job_id);
        }).flatMap((downloads: any) => {
            this.downloads = downloads;
            return this.jobService.getEnv(project_id, job_id);
        }).subscribe((e: EnvironmentVariable[]) => {
            this.environment = e;

            this.cli_command = `export INFRABOX_CLI_TOKEN=<YOUR_TOKEN>\ninfrabox pull`;

            for (const v of e) {
                this.cli_command += ` \\\n    -e "${v.name}=${v.value}"`;
            }

            this.cli_command += ` \\\n    --job-id ${job_id}`;
            this.ready = true;
        });
    }

    public ngOnDestroy(): void {
        this.unsubscribe();
    }

    private unsubscribe() {
        if (this.sub) {
            this.sub.unsubscribe();
        }
    }
}
