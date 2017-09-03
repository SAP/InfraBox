import { Component, OnInit, OnDestroy } from "@angular/core";

import { Subscription } from "rxjs";

import { UserService, AuthToken } from "../services/user.service";
import { Notification, NotificationService } from "../services/notification.service";

@Component({
    selector: "auth-token",
    templateUrl: "./auth_token.component.html"
})
export class AuthTokenComponent implements OnInit, OnDestroy {
    private subs = new Array<Subscription>();
    private tokens: AuthToken[];
    private add_token = new AuthToken();

    constructor(private userService: UserService, private notificationService: NotificationService) {}

    public ngOnDestroy() {
        for (let s of this.subs) {
            s.unsubscribe();
        }
    }

    public ngOnInit() {
        this.getTokens();
    }

    public delete(t: AuthToken) {
        this.userService.deleteAuthToken(t).subscribe((n: Notification) => {
            this.notificationService.notify(n);
            this.getTokens();
        });
    }

    public add() {
        this.userService.addAuthToken(this.add_token).subscribe((n: Notification) => {
            this.notificationService.notify(n);
            this.getTokens();
        });

        this.add_token = new AuthToken();
    }

    private getTokens() {
        this.tokens = new Array<AuthToken>();
        this.subs.push(this.userService.getAuthTokens().subscribe((token: AuthToken) => {
            this.tokens.push(token);
        }));
    }
}
