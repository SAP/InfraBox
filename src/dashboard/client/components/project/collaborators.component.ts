import { Component, OnInit, OnDestroy, Input } from "@angular/core";
import { Subscription } from "rxjs/Subscription";

import { User } from "../../services/user.service";
import { Project, ProjectService } from "../../services/project.service";
import { Notification, NotificationService } from "../../services/notification.service";

@Component({
    selector: "project-collaborators",
    templateUrl: "./collaborators.component.html"
})
export class ProjectCollaboratorsComponent implements OnInit, OnDestroy {
    @Input() private project: Project;
    private collaborators: User[];
    private subs = new Array<Subscription>();

    constructor(private projectService: ProjectService, private notificationService: NotificationService) { }

    public ngOnInit(): void {
        this.getCollaborators();
    }

    private getCollaborators() {
        this.collaborators = new Array<User>();
        this.subs.push(this.projectService.getCollaborators(this.project.id).subscribe((c: User) => {
            this.collaborators.push(c);
        }));
    }

    public remove(c: User) {
        this.subs.push(this.projectService.removeCollaborator(this.project.id, c.id).subscribe((n: Notification) => {
            this.notificationService.notify(n);
            this.getCollaborators();
        }));
    }

    public onSubmit(form: any): void {
        this.subs.push(this.projectService.addCollaborator(this.project.id, form.username).subscribe((n: Notification) => {
            this.notificationService.notify(n);
            this.getCollaborators();
        }));
    }

    private unsubscribe() {
        if (!this.subs) {
            return;
        }

        for (let s of this.subs) {
            s.unsubscribe();
        }

        this.subs = null;
    }

    public ngOnDestroy() {
        this.unsubscribe();
    }
}
