import { Component, Input, OnInit, OnDestroy } from "@angular/core";

import { Subscription } from "rxjs";

import { ProjectService, AuthToken } from "../../services/project.service";
import { Notification, NotificationService } from "../../services/notification.service";

@Component({
    selector: "project-token",
    templateUrl: "./token.component.html"
})
export class AuthTokenComponent implements OnInit, OnDestroy {
    @Input() private project_id: string;

    private subs = new Array<Subscription>();
    private tokens: AuthToken[];
    private add_token = new AuthToken();

    constructor(private projectService: ProjectService,
        private notificationService: NotificationService) {}

    public ngOnDestroy() {
        for (let s of this.subs) {
            s.unsubscribe();
        }
    }

    public ngOnInit() {
        this.getTokens();
    }

    public delete(t: AuthToken) {
        this.projectService.deleteAuthToken(this.project_id, t).subscribe((n: Notification) => {
            this.notificationService.notify(n);
            this.getTokens();
        });
    }

    public add() {
        this.projectService.addAuthToken(this.project_id, this.add_token).subscribe((n: Notification) => {
            this.notificationService.notify(n);
            this.getTokens();
        });

        this.add_token = new AuthToken();
    }

    private getTokens() {
        this.tokens = new Array<AuthToken>();
        this.subs.push(this.projectService.getAuthTokens(this.project_id).subscribe((token: AuthToken) => {
            this.tokens.push(token);
        }));
    }
}
