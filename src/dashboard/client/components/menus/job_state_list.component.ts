import { Component, OnDestroy, Input, OnInit } from "@angular/core";
import { Subscription } from "rxjs/Subscription";
import { BehaviorSubject } from "rxjs/BehaviorSubject";
import { Observable } from "rxjs/Observable";

import { JobState } from "../../services/job.service";
import { LogService, Logger } from "../../services/log.service";
import { ProjectService, Project } from "../../services/project.service";
import { Build, BuildService } from "../../services/build.service";
import { UserService } from "../../services/user.service";

@Component({
    selector: "job-state-list",
    template: `
<li class="dropdown">
    <a *ngIf="stateToShow==='active' && builds.length > 0" class="dropdown-toggle count-info" data-toggle="dropdown" href="#">
       <span class="label-counter label-info">{{ builds.length }}</span><span class="text-muted small">Builds Running</span>
    </a>
    <a *ngIf="stateToShow==='active' && builds.length == 0" class="dropdown-toggle count-info">
        <span class="label-counter label-info">{{ builds.length }}</span><span class="text-muted small">Builds Running</span>
    </a>

    <a *ngIf="stateToShow!=='active' && builds.length > 0" class="dropdown-toggle count-info" data-toggle="dropdown" href="#">
        <span class="label-counter label-danger">{{ builds.length }}</span><span class="text-muted small">Builds Failed</span>
    </a>
    <a *ngIf="stateToShow!=='active' && builds.length == 0" class="dropdown-toggle count-info">
        <span class="label-counter label-danger">{{ builds.length }}</span><span class="text-muted small">Builds Failed</span>
    </a>

    <ul role="menu" class="dropdown-menu" style="text-align: left; list-style-type: none; padding-left: 0; margin-left: 0">
        <li *ngFor="let b of builds" class="m-sm p-b-xs">
            <a *ngIf="b.commit" [routerLink]="['/dashboard/project', b.project.id, 'build', b.id]" class="inherit-style" style="text-align: left; list-style-type: none; padding-left: 0; margin-left: 0">
                <job-state  class="small" [state]="b.getState()"></job-state>
                <span class="nav-label small">{{ b.project.name }} - {{ b.number }}.{{ b.restart_counter }}</span>
            </a>
            <a *ngIf="!b.commit" [routerLink]="['/dashboard/project', b.project.id]" class="inherit-style" style="text-align: left; padding-left: 0; margin-left: 0">
                <job-state class="small" [state]="b.getState()"></job-state>
                <span class="nav-label small">{{ b.project.name }} - {{ b.number }}.{{ b.restart_counter }}</span>
            </a>
        </li>
    </ul>
</li>
`,
})

export class JobStateListComponent implements OnInit, OnDestroy {
    @Input() public stateToShow: string;
    private logger: Logger;
    private builds = new Array<Build>();
    private subs = new Array<Subscription>();

    constructor(private logService: LogService,
        private projectService: ProjectService,
        private buildService: BuildService,
        private userService: UserService) {
        this.logger = logService.createNamedLogger("JobStateListComponent");
    }

    public ngOnInit(): void {
        this.subs.push(this.projectService.getProjects().subscribe((project: Project) => {
            this.subs.push(this.buildService.getBuildsForProject(project.id).subscribe((b: Build) => {
                if (this.stateToShow === 'active') {
                    if (b.getStateValue() === 'running' || b.getStateValue() === 'scheduled' || b.getStateValue() === 'queued') {
                        this.add(b);

                        this.subs.push(b.getState().subscribe((s: JobState) => {
                            if (s === "failure" || s === "killed" || s === "finished" || s === "error") {
                                this.remove(b);
                            }
                        }));
                    } else if (b.getStateValue() === 'finished') {
                        // we may see them as finished, because not all jobs have been loaded yet
                        this.subs.push(b.getState().subscribe((s: JobState) => {
                            if (s === 'running' || s === 'scheduled' || s === 'queued') {
                                this.add(b);
                            }

                            this.subs.push(b.getState().subscribe((js: JobState) => {
                                if (js === "failure" || js === "killed" || js === "finished" || js === "error") {
                                    this.remove(b);
                                }
                            }));
                        }));
                    }

                } else {
                    if (b.getStateValue() === 'failure' || b.getStateValue() === 'error') {
                        this.builds.unshift(b);

                        if (this.builds.length > 5) {
                            this.builds.pop();
                        }
                    }
                }
           }));
        }));
    }

    private add(b: Build) {
        let found = false;
        for (let i of this.builds) {
            if (i.id === b.id) {
                found = true;
            }
        }

        if (!found) {
            this.builds.unshift(b);
        }
    }

    private remove(b: Build) {
        for (let i  = 0; i < this.builds.length; ++i) {
            if (this.builds[i].id === b.id) {
                this.builds.splice(i, 1);
            }
        }
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
