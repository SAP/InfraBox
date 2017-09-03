import { Component, Input } from "@angular/core";

import { TestState } from "../../services/test.service";

@Component({
    selector: "test-state",
    template: `
    {{ result }}
    <span *ngIf="state=='skipped'"    data-toggle="tooltip" title="skipped"><i class="fa fa-step-forward icon-neutral-negative btn-circle-small"></i></span>
    <span *ngIf="state=='ok'"         data-toggle="tooltip" title="ok"><i class="fa fa-check icon-success-negative btn-circle-small"></i></span>
    <span *ngIf="state=='failure'"    data-toggle="tooltip" title="failure"><i class="fa fa-bolt icon-failure-negative btn-circle-small"></i></span>
    <span *ngIf="state=='error'"      data-toggle="tooltip" title="error"><i class="fa fa-bomb icon-error-negative btn-circle-small"></i></span>
    `,
})
export class TestStateComponent {
    @Input() private state: TestState; // tslint:disable-line
}
