import { Component, Input } from "@angular/core";

import { Job } from "../../../services/job.service";

@Component({
    selector: "job-list",
    templateUrl: "./list.component.html"
})
export class JobListComponent {
    @Input() private jobs: Job[] = []; // tslint:disable-line
}
