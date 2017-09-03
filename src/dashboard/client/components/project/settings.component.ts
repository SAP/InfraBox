import { Component, OnDestroy, OnInit } from "@angular/core";
import { Router } from "@angular/router";
import { ActivatedRoute } from "@angular/router";

import { Subscription } from "rxjs/Subscription";

import { ProjectService, Project } from "../../services/project.service";
import { NotificationService, Notification } from "../../services/notification.service";

@Component({
    selector: "project-settings",
    templateUrl: "./settings.component.html",
})
export class ProjectSettingsComponent implements OnInit, OnDestroy {
    private project: Project;
    private subs: Subscription[];
    private host: string;

    constructor(private projectService: ProjectService,
        private route: ActivatedRoute,
        private router: Router,
        private notificationService: NotificationService) {
        this.host = window['INFRABOX_API_URL'];
    }

    private init(): void {
        this.unsubscribe();
        this.subs = new Array<Subscription>();
    }

    public ngOnInit(): void {
        this.route.params.subscribe((params) => {
            this.init();

            const project_id = params["project_id"];

            const sub_repo = this.projectService.getProject(project_id).subscribe((r: Project) => {
                this.project = r;
            });
            this.subs.push(sub_repo);
        });
    }

    public deleteProject() {
        this.subs.push(this.projectService.deleteProject(this.project.id).subscribe((n: Notification) => {
            this.notificationService.notify(n);

            if (n.type === "success") {
                setTimeout(() => {
                    window.location.href = "/dashboard/start";
                }, 2000);
            }
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

    public ngOnDestroy() {
        this.unsubscribe();
    }
}
