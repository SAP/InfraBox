import { Component, Input, OnInit, OnDestroy } from "@angular/core";
import { SimpleChanges, OnChanges } from "@angular/core/index";

import { Subscription } from "rxjs";
import { Observable } from "rxjs/Observable";

@Component({
    selector: "start-date",
    template: `
    <span *ngIf="start_value">{{ start_value | amCalendar }}</span>
    <span *ngIf="!start_value">not started yet</span>
    `,
})
export class StartDateComponent implements OnInit, OnDestroy, OnChanges {
    @Input() private start: Observable<Date>;
    private start_value: Date;
    private subscription: Subscription;

    public ngOnChanges(changes: SimpleChanges) {
        this.init();
    }

    public ngOnInit() {
        this.init();
    }

    public init() {
        if (this.start.subscribe) {
            this.subscription = this.start.subscribe((d: Date) => {
                this.start_value = d;
            });
        } else {
            this.start_value = this.start as any;
        }
   }

    public ngOnDestroy() {
        if (this.subscription) {
            this.subscription.unsubscribe();
        }
    }
}
