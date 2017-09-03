import { Component, OnDestroy, OnInit } from "@angular/core";
import { Subscription } from "rxjs/Subscription";
import { BehaviorSubject } from "rxjs/BehaviorSubject";
import { Observable } from "rxjs/Observable";

import { JobState } from "../../services/job.service";
import { LogService, Logger } from "../../services/log.service";
import { ProjectService, Project } from "../../services/project.service";
import { Build, BuildService } from "../../services/build.service";
import { UserService } from "../../services/user.service";

class Branch {
    public state: BehaviorSubject<JobState>;
    public sub: Subscription;

    constructor(public name: string, public latest_build: Build) {
        this.state = new BehaviorSubject<JobState>(latest_build.getStateValue());
        this.setBuild(latest_build);
    }

    public setBuild(b: Build) {
        if (this.sub) {
            this.sub.unsubscribe();
        }

        this.latest_build = b;
        this.sub = b.getState().subscribe(this.state);
    }

    public getState(): Observable<JobState> {
        return this.state;
    }
}

class ProjectEntry {
    public branches = new Array<Branch>();
    constructor(public project: Project) { }
}

@Component({
    selector: "project-list",
    template: `
    <li [routerLinkActive]="['active']" *ngFor="let r of projects" class="m-sm m-b-md">
        <a [routerLink]="['/dashboard/project', r.project.id]" class="inherit-style m-b-md">
             <i *ngIf="r.project.type == 'github'" class="fa fa-github" aria-hidden="true"></i>
             <i *ngIf="r.project.type == 'upload'" class="fa fa-upload" aria-hidden="true"></i>
             <i *ngIf="r.project.type == 'gerrit'" class="fa fa-git" aria-hidden="true"></i>
             <span class="nav-label">{{ r.project.name }}</span>
        </a>
    </li>
`,
})

export class RepoListComponent implements OnInit, OnDestroy {
    private projects = new Array<ProjectEntry>();
    private sub_builds: Subscription;
    private sub_repos: Subscription;

    constructor(private logService: LogService,
        private projectService: ProjectService,
        private buildService: BuildService,
        private userService: UserService) {
    }

    public ngOnInit(): void {
        if (!this.userService.isLoggedIn()) {
            return;
        }

        this.sub_repos = this.projectService.getProjects().subscribe((project: Project) => {
            const re = new ProjectEntry(project);
            this.projects.push(re);
            this.updateBuildForRepositroy(re);
        });
    }

    public ngOnDestroy() {
        this.sub_builds.unsubscribe();
        this.sub_repos.unsubscribe();
    }

    private updateBuildForRepositroy(r: ProjectEntry) {
        this.buildService.getBuildsForProject(r.project.id).subscribe((build: Build) => {
            if (build.commit) {
                for (const b of r.branches) {
                    if (b.name === build.commit.branch) {
                        b.setBuild(build);
                        return;
                    }
                }

                const b = new Branch(build.commit.branch, build);
                r.branches.push(b);
            } else {
                if (r.branches.length === 0) {
                    const b = new Branch("Builds", build);
                    r.branches.push(b);
                } else {
                    r.branches[0].setBuild(build);
                }
            }
        });
    }
}
