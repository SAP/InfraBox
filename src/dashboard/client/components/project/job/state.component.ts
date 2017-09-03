import { Component, OnInit, Input, OnDestroy } from "@angular/core";
import { SimpleChanges, OnChanges } from "@angular/core/index";

import { JobState } from "../../../services/job.service";
import { Subscription } from "rxjs";
import { Observable } from "rxjs/Observable";

@Component({
    selector: "job-state",
    template: `
    <span *ngIf="value=='queued' && negative"     data-toggle="tooltip" title="queued"><i class="fa fa-pause-circle-o icon-paused-negative btn-circle-small"></i></span>
    <span *ngIf="value=='scheduled' && negative"  data-toggle="tooltip" title="scheduled"><i class="fa fa-th-list icon-scheduled-negative btn-circle-small"></i></span>
    <span *ngIf="value=='running' && negative"    data-toggle="tooltip" title="running"><i class="fa fa-dot-circle-o icon-running-negative btn-circle-small"></i></span>
    <span *ngIf="value=='finished' && negative"   data-toggle="tooltip" title="finished"><i class="fa fa-check icon-success-negative btn-circle-small"></i></span>
    <span *ngIf="value=='skipped' && negative"    data-toggle="tooltip" title="skipped"><i class="fa fa-share icon-skipped-negative btn-circle-small"></i></span>
    <span *ngIf="value=='failure' && negative"    data-toggle="tooltip" title="failure"><i class="fa fa-bolt icon-failure-negative btn-circle-small"></i></span>
    <span *ngIf="value=='error' && negative"      data-toggle="tooltip" title="error"><i class="fa fa-bomb icon-error-negative btn-circle-small"></i></span>
    <span *ngIf="value=='killed' && negative"     data-toggle="tooltip" title="killed"><i class="fa fa-ban icon-white-negative btn-circle-small"></i></span>

    <span *ngIf="value=='queued' && !negative"     data-toggle="tooltip" title="queued"><i class="fa fa-pause-circle-o icon-paused"></i></span>
    <span *ngIf="value=='scheduled' && !negative"  data-toggle="tooltip" title="scheduled"><i class="fa fa-th-list icon-scheduled"></i></span>
    <span *ngIf="value=='running' && !negative"    data-toggle="tooltip" title="running"><i class="fa fa-dot-circle-o icon-running"></i></span>
    <span *ngIf="value=='finished' && !negative"   data-toggle="tooltip" title="finished"><i class="fa fa-check icon-success"></i></span>
    <span *ngIf="value=='skipped' && !negative"    data-toggle="tooltip" title="skipped"><i class="fa fa-share icon-mute"></i></span>
    <span *ngIf="value=='failure' && !negative"    data-toggle="tooltip" title="failure"><i class="fa fa-bolt icon-failure"></i></span>
    <span *ngIf="value=='error' && !negative"      data-toggle="tooltip" title="error"><i class="fa fa-bomb icon-error"></i></span>
    <span *ngIf="value=='killed' && !negative"     data-toggle="tooltip" title="killed"><i class="fa fa-ban icon-grey"></i></span>
    `,
})
export class JobStateComponent implements OnInit, OnDestroy, OnChanges {
    @Input() private state: Observable<JobState>;
    @Input() private negative = true; // tslint:disable-line
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
