import { Component, OnInit, Input, OnDestroy } from "@angular/core";
import { SimpleChanges, OnChanges } from "@angular/core/index";

import { Subscription } from "rxjs";
import { Observable } from "rxjs/Observable";

@Component({
    selector: "duration",
    template: `
    <span *ngIf="end_value && start_value">{{ end_value - start_value | amDuration: 'milliseconds' }}</span>
    <span *ngIf="!end_value">not finished yet</span>
    `,
})
export class DurationComponent implements OnInit, OnDestroy, OnChanges {
    @Input() private start: Observable<Date>;
    @Input() private end: Observable<Date>;
    private end_value: Date;
    private start_value: Date;
    private start_sub: Subscription;
    private end_sub: Subscription;

    public ngOnInit() {
        this.init();
    }

    public init() {
        this.ngOnDestroy();

        this.end_sub = this.end.subscribe((d: Date) => {
            this.end_value = d;
        });

        this.start_sub = this.start.subscribe((d: Date) => {
            this.start_value = d;
        });
    }

    public ngOnChanges(changes: SimpleChanges) {
        this.init();
    }

    public ngOnDestroy() {
        if (this.start_sub) {
            this.start_sub.unsubscribe();
        }

        if (this.end_sub) {
            this.end_sub.unsubscribe();
        }
    }
}
