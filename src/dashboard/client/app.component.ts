import { Component, OnInit, OnDestroy } from "@angular/core";

import { Observable } from "rxjs/Observable";
import { Subscription } from "rxjs/Subscription";

import { NotificationService, Notification } from "./services/notification.service";
import { UserService } from "./services/user.service";
import { Logger, LogService } from "./services/log.service";
import { GithubRepo, ProjectService, ProjectType } from "./services/project.service";
import { LoginService } from "./services/login.service";
import { InfraBoxService } from "./services/infrabox.service";

import toastr = require("toastr");
require('./img/dashboard/logo_white_on_transparent.png');

@Component({
    selector: "benchbox-app",
    templateUrl: "./app.component.html"
})
export class AppComponent implements OnInit, OnDestroy {
    private subs = new Array<Subscription>();
    private logger: Logger;

    constructor(
        private notificationService: NotificationService,
        private loginService: LoginService,
        private logService: LogService,
        private projectService: ProjectService,
        private userService: UserService,
        private infraboxService: InfraBoxService) {
        this.logger = this.logService.createNamedLogger("AppComponent");

        toastr.options = {
            closeButton: true,
            debug: false,
            progressBar: true,
            preventDuplicates: false,
            positionClass: 'toast-top-center',
            onclick: null,
            showDuration: 400,
            hideDuration: 1000,
            timeOut: 7000,
            extendedTimeOut: 1000,
            showEasing: 'swing',
            hideEasing: 'linear',
            showMethod: 'fadeIn',
            hideMethod: 'fadeOut'
        };
    }

    public ngOnInit() {
        this.subs.push(this.notificationService.getNotifications().subscribe((n: Notification) => {
            if (n.type === "error") {
                toastr.error(n.message);
            } else if (n.type === "success") {
                toastr.success(n.message);
            } else {
                this.logger.error("Unknown notification type", n);
            }
        }));
    }

    public logout() {
        this.loginService.logout();
    }

    public ngOnDestroy() {
        for (const s of this.subs) {
            s.unsubscribe();
        }
    }
}
