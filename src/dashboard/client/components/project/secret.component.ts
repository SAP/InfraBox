import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs/Subscription';

import { Secret, ProjectService } from '../../services/project.service';
import { Notification, NotificationService } from '../../services/notification.service';

@Component({
    selector: 'secret-table',
    templateUrl: "./secret.component.html"
})
export class SecretComponent implements OnInit, OnDestroy {
    @Input() private project_id: string;

    private subs = new Array<Subscription>();
    private vars: Secret[];
    private new_name: string;
    private new_value: string;

    constructor(private projectService: ProjectService, private notificationService: NotificationService) {}

    public ngOnInit() {
        this.getVars();
    }

    public ngOnDestroy() {
        this.unsubscribe();
    }

    public delete(e: Secret) {
        this.subs.push(this.projectService.deleteSecret(this.project_id, e.id).subscribe((n: Notification) => {
            this.notificationService.notify(n);
            this.getVars();
        }));
    }

    public add() {
        const e = new Secret(this.new_name, this.new_value, null);

        this.subs.push(this.projectService.addSecret(this.project_id, e).subscribe((n: Notification) => {
            this.notificationService.notify(n);
            this.new_name = "";
            this.new_value = "";
            this.getVars();
        }));
    }

    private getVars() {
        this.vars = new Array<Secret>();
        this.subs.push(this.projectService.getSecrets(this.project_id).subscribe((e: Secret) => {
            this.vars.push(e);
        }));
    }

    private unsubscribe() {
        if (!this.subs) {
            return;
        }

        for (const s of this.subs) {
            s.unsubscribe();
        }

        this.subs = null;
    }
}
