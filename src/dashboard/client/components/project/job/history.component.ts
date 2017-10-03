import { Component, OnInit, OnDestroy, Input } from "@angular/core";
import { Subscription } from "rxjs/Subscription";

import { Job, JobService } from "../../../services/job.service";
import { ActivatedRoute } from "@angular/router";

@Component({
    selector: "job-history",
    templateUrl: "./history.component.html"
})
export class JobHistoryComponent implements OnInit, OnDestroy {
    private sub: Subscription;
    private job: Job;
    private jobs: Job[] = [];

    constructor(private jobService: JobService,
                private route: ActivatedRoute) {}

    public ngOnInit(): void {
       this.route.parent.params.flatMap((params) => {
            const job_id = params["job_id"];
            return this.jobService.getJob(job_id);
        }).flatMap((j: Job) => {
            this.job = j;
            return this.jobService.getJobs();
        }).filter((j: Job) => {
            if (j.project_id !== this.job.project_id) {
                return false;
            }

            if (j.name !== this.job.name) {
                return false;
            }

            if (j.commit && this.job.commit) {
                if (j.commit.branch === this.job.commit.branch) {
                    return true;
                }
            }

            if (!j.commit && !this.job.commit) {
                return true;
            }

            return false;
        }).subscribe((j: Job) => {
            this.jobs.unshift(j);
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
