import { Component, OnInit, Input, OnDestroy } from "@angular/core";
import { SimpleChanges, OnChanges } from "@angular/core/index";

import { JobState } from "../../../services/job.service";
import { Subscription } from "rxjs";
import { Observable } from "rxjs/Observable";

@Component({
    selector: "job-state-big",
    template: `

<div *ngIf="value=='queued'" class="state-widget bb-bg-neutral">
    <i class="fa fa-pause-circle-o fa-4x"></i>
    <h1 class="m-xs">QUEUED</h1>
</div>

<div *ngIf="value=='scheduled'" class="state-widget bb-bg-grey">
    <i class="fa fa-th-list fa-4x"></i>
    <h1 class="m-xs">SCHEDULED</h1>
</div>

<div *ngIf="value=='running'" class="state-widget bb-bg-running">
    <i class="fa fa-dot-circle-o fa-4x"></i>
    <h1 class="m-xs">RUNNING</h1>
</div>

<div *ngIf="value=='finished'" class="state-widget bb-bg-success">
    <i class="fa fa-check fa-4x"></i>
    <h1 class="m-xs">OK</h1>
</div>

<div *ngIf="value=='skipped'" class="state-widget bb-bg-grey">
    <i class="fa fa-share fa-4x"></i>
    <h1 class="m-xs">SKIPPED</h1>
</div>

<div *ngIf="value=='failure'" class="state-widget bb-bg-failure">
    <i class="fa fa-bolt fa-4x"></i>
    <h1 class="m-xs">FAILURE</h1>
</div>

<div *ngIf="value=='error'" class="state-widget bb-bg-error">
    <i class="fa fa-bomb fa-4x"></i>
    <h1 class="m-xs">ERROR</h1>
</div>

<div *ngIf="value=='killed'" class="state-widget bb-bg-grey">
    <i class="fa fa-ban fa-4x"></i>
    <h1 class="m-xs">KILLED</h1>
</div>

    `,
})
export class JobStateBigComponent implements OnInit, OnDestroy, OnChanges {
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
