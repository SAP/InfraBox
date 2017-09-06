import { Component, OnInit, OnDestroy} from "@angular/core";
import { Router } from "@angular/router";

import { Notification, NotificationService} from "../services/notification.service";
import { UserService } from "../services/user.service";
import { Subscription, Observable } from "rxjs";
import { Logger, LogService } from "../services/log.service";
import { GithubRepo, ProjectService, ProjectType } from "../services/project.service";
import { InfraBoxService } from "../services/infrabox.service";

@Component({
    selector: "add-project",
    templateUrl: "./add_project.component.html"
})
export class AddProjectComponent implements OnInit, OnDestroy {
    private subs = new Array<Subscription>();
    private repos = new Array<GithubRepo>();
    private logger: Logger;
    private add_project_name: string;
    private add_project_private: boolean = true;
    private add_project_type: ProjectType = "upload";
    private add_project_repo: GithubRepo;
    private hasGithubAccount = false;

    constructor(
        private notificationService: NotificationService,
        private logService: LogService,
        private projectService: ProjectService,
        private userService: UserService,
        private infraboxService: InfraBoxService) {
        this.logger = this.logService.createNamedLogger("AppComponent");
    }

    public ngOnInit() {
        this.subs.push(this.userService.hasGithubAccount().flatMap((hasAccount: boolean) => {
            this.hasGithubAccount = hasAccount;

            if (hasAccount) {
                return this.projectService.getGithubRepositories();
            } else {
                return Observable.from([]);
            }
        }).subscribe((r: GithubRepo) => {
            this.repos.push(r);
        }));
    }

    public setProjectType(t: ProjectType) {
        this.add_project_type = t;
    }

    public setPrivate(b: boolean) {
        this.add_project_private = b;
    }

    public connectGithubAccount() {
        window.location.href = "/github/auth/connect";
    }

    public select(r: GithubRepo) {
        this.add_project_name = r.owner.login + "/" + r.name;
    }

    public addProject() {
        if (!this.add_project_name) {
            return;
        }

        this.subs.push(this.projectService.addProject(this.add_project_name,
                                                      this.add_project_private,
                                                      this.add_project_type)
                       .subscribe((n: Notification) => {
            this.notificationService.notify(n);
            if (n.type === "success") {
                setTimeout(() => {
                    window.location.href = "/dashboard/project/" + n.data.project_id;
                }, 2000);
            }
        }));
    }

    public ngOnDestroy() {
        for (const s of this.subs) {
            s.unsubscribe();
        }
    }
}
