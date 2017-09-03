import { Component, OnInit, Input, OnDestroy } from "@angular/core";
import { SimpleChanges, OnChanges } from "@angular/core/index";

import { JobState } from "../../../services/job.service";
import { Subscription } from "rxjs";
import { Observable } from "rxjs/Observable";

@Component({
    selector: "job-state-timeline",
    template: `
    <div *ngIf="value=='queued'" data-toggle="tooltip" title="queued" class="vertical-timeline-icon bb-bg-white"><i class="fa fa-th-list"></i></div>
    <div *ngIf="value=='scheduled'" data-toggle="tooltip" title="scheduled" class="vertical-timeline-icon bb-bg-neutral"><i class="fa fa-pause-circle-o"></i></div>
    <div *ngIf="value=='running'" data-toggle="tooltip" title="running" class="vertical-timeline-icon bb-bg-running"><i class="fa fa-dot-circle-o"></i></div>
    <div *ngIf="value=='finished'" data-toggle="tooltip" title="finished" class="vertical-timeline-icon bb-bg-success"><i class="fa fa-check"></i></div>
    <div *ngIf="value=='skipped'" data-toggle="tooltip" title="skipped" class="vertical-timeline-icon bb-bg-neutral"><i class="fa fa-share"></i></div>
    <div *ngIf="value=='failure'" data-toggle="tooltip" title="failure" class="vertical-timeline-icon bb-bg-failure"><i class="fa fa-bolt"></i></div>
    <div *ngIf="value=='error'" data-toggle="tooltip" title="error" class="vertical-timeline-icon bb-bg-black"><i class="fa fa-bomb"></i></div>
    <div *ngIf="value=='killed'" data-toggle="tooltip" title="killed" class="vertical-timeline-icon bb-bg-neutral"><i class="fa fa-ban"></i></div>
    `,
})
export class JobStateTimelineComponent implements OnInit, OnDestroy {
    @Input() private state: Observable<JobState>;
    private value: JobState;
    private subscription: Subscription;

    public ngOnChanges(changes: SimpleChanges) {
        this.init();
    }

    public ngOnInit() {
        this.init();
    }

    public init() {
        this.ngOnDestroy();

        this.subscription = this.state.subscribe((s: JobState) => {
            this.value = s;
        });
    }

    public ngOnDestroy() {
        if (this.subscription) {
            this.subscription.unsubscribe();
        }
    }
}
