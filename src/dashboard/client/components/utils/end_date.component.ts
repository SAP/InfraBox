import { Component, OnInit, Input, OnDestroy } from "@angular/core";

import { Subscription } from "rxjs";
import { Observable } from "rxjs/Observable";

@Component({
    selector: "end-date",
    template: `
    <span *ngIf="end_value">{{ end_value | amCalendar }}</span>
    <span *ngIf="!end_value">not finished yet</span>
    `,
})
export class EndDateComponent implements OnInit, OnDestroy {
    @Input() private end: Observable<Date>;
    private end_value: Date;
    private subscription: Subscription;

    public ngOnInit() {
        this.subscription = this.end.subscribe((d: Date) => {
            this.end_value = d;
        });
    }

    public ngOnDestroy() {
        this.subscription.unsubscribe();
    }
}
