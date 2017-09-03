import { Component, OnInit, OnDestroy} from "@angular/core";
import { Router } from "@angular/router";

import { Notification, NotificationService} from "../services/notification.service";
import { GithubRepo, ProjectService } from "../services/project.service";
import { UserService } from "../services/user.service";

import { Subscription, Observable } from "rxjs";

@Component({
    selector: "github-repos",
    templateUrl: "./github_repos.component.html"
})
export class GithubReposComponent implements OnInit, OnDestroy {
    private repos = new Array<GithubRepo>();
    private sub: Subscription;
    private hasGithubAccount = false;

    constructor(private router: Router,
        private projectService: ProjectService,
        private userService: UserService,
        private notificationService: NotificationService) {}

    public ngOnInit() {
        this.sub = this.userService.hasGithubAccount().flatMap((hasAccount: boolean) => {
            this.hasGithubAccount = hasAccount;

            if (hasAccount) {
                return this.projectService.getGithubRepositories();
            } else {
                return Observable.from([]);
            }
        }).subscribe((r: GithubRepo) => {
            this.repos.push(r);
        });
    }

    public ngOnDestroy() {
        this.sub.unsubscribe();
    }

    public connectGithubAccount() {
        window.location.href = "/github/auth/connect";
    }

    public connect(r: GithubRepo) {
        this.sub = this.projectService.connectGithubRepo(r.owner.login, r.name).subscribe((n: Notification) => {
            this.notificationService.notify(n);

            if (n.type === "success") {
                setTimeout(() => {
                    window.location.href = "/dashboard/account/repositories";
                }, 1000);
            }
        });
    }
}
