import { Component, OnInit, OnDestroy, Input } from "@angular/core";
import { Subscription } from "rxjs/Subscription";

import { Job, JobService } from "../../../services/job.service";
import { ActivatedRoute } from "@angular/router";

@Component({
    selector: "job-downloads",
    templateUrl: "./downloads.component.html"
})
export class JobDownloadsComponent implements OnInit, OnDestroy {
    private sub: Subscription;
    private downloads: any;
    private project_id = null;
    private job_id = null;

    constructor(private jobService: JobService,
                private route: ActivatedRoute) {}

    public ngOnInit(): void {
        this.sub = this.route.parent.params.flatMap((params) => {
            this.project_id = params["project_id"];
            this.job_id = params["job_id"];
            return this.jobService.getDownloads(this.project_id, this.job_id);
        }).subscribe((downloads: any) => {
            if (Object.keys(downloads).length !== 0) {
                this.downloads = downloads;
            }
        });
    }

    public download(file_id, file_name) {
        this.jobService.getDownload(this.project_id, this.job_id, file_id, file_name);
    }

    public ngOnDestroy(): void {
        if (this.sub) {
            this.sub.unsubscribe();
        }
    }
}
