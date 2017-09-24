import { Injectable } from "@angular/core";
import { Observable } from "rxjs/Observable";
import { APIService } from "./api.service";
import { Notification } from "./notification.service";
import { User } from "./user.service";
import { JobService } from "./job.service";

import "rxjs/add/operator/map";
import "rxjs/add/operator/do";
import 'rxjs/add/operator/single';
import 'rxjs/add/operator/mergeMap';
import 'rxjs/add/observable/from';

type RepoType = "github" | "upload" | "gerrit";
export type ProjectType = "gerrit" | "github" | "upload";

export class GithubUser {
    public login: string;
}

export class GithubRepo {
    public name: string;
    public connected: boolean;
    public owner: GithubUser;
}

export class Project {
    public id: string;
    public name: string;
    public type: RepoType;
}

export class Secret {
    constructor(public name: string, public value: string, public id: string) {}
}

export class AuthToken {
    public id: string;
    public description: string;
    public token: string;
    public scope_push = false;
    public scope_pull = false;
}

@Injectable()
export class ProjectService {
    private projectURL = "api/dashboard/project";
    private projects = new Array<Project>();
    private githubRepos: GithubRepo[];

    constructor(private api: APIService, private jobService: JobService) {}

    public getGithubRepositories(): Observable<GithubRepo> {
        if (this.githubRepos) {
            return Observable.from(this.githubRepos);
        }

        return this.api.get("api/dashboard/github/repos").mergeMap((repos: GithubRepo[]) => {
            return Observable.from(repos);
        });
    }

    public addAuthToken(project_id: string, token: AuthToken): Observable<Notification> {
        const url = this.projectURL + '/' + project_id + '/tokens';
        const body = JSON.stringify({
            description: token.description,
            token: token.token,
            scope_pull: token.scope_pull,
            scope_push: token.scope_push
        });
        return this.api.post(url, body);
    }

    public deleteAuthToken(project_id: string, token: AuthToken): Observable<Notification> {
        const url = this.projectURL + '/' + project_id + '/tokens/' + token.id;
        return this.api.delete(url);
    }

    public getAuthTokens(project_id: string): Observable<AuthToken> {
        const url = this.projectURL + '/' + project_id + '/tokens';

        return this.api.get(url).mergeMap((env: AuthToken[]) => {
            return Observable.from(env);
        });
    }

    public connectGithubRepo(owner: string, repo: string): Observable<Notification> {
        const url = 'api/dashboard/github/repo/' + owner + "/" + repo + '/connect';
        return this.api.post(url, "{}");
    }

    public getProjects(): Observable<Project> {
        if (this.projects && this.projects.length > 0) {
            return Observable.from(this.projects);
        }

        return this.api.get(this.projectURL).mergeMap((p: Project[]) => {
            this.projects = p;

            for (const pro of p) {
                this.jobService.startListening(pro.id);
            }

            return Observable.from(p);
        });
    }

    private getCachedProject(project_id: string): Project {
        for (const p of this.projects) {
            if (p.id === project_id) {
                return p;
            }
        }

        return null;
    }

    public getProject(project_id: string): Observable<Project> {
        const p = this.getCachedProject(project_id);

        if (p) {
            return Observable.from([p]);
        }

        const url = this.projectURL + '/' + project_id;
        return this.api.get(url).mergeMap((project: Project) => {
            this.projects.push(project);
            this.jobService.startListening(project_id);
            return Observable.from([project]);
        });
    }

    public getCollaborators(project_id: string): Observable<User> {
        const url = this.projectURL + '/' + project_id + '/collaborators';

        return this.api.get(url).mergeMap((collabs: User[]) => {
            return Observable.from(collabs);
        });
    }

    public addProject(name: string, priv: boolean, t: ProjectType): Observable<Notification> {
        const url = this.projectURL;
        const body = JSON.stringify({ name: name, type: t, private: priv });
        return this.api.post(url, body);
    }

    public addCollaborator(project_id: string, username: string): Observable<Notification> {
        const url = this.projectURL + '/' + project_id + '/collaborators';
        const body = JSON.stringify({ username: username });
        return this.api.post(url, body);
    }

    public removeCollaborator(project_id: string, user_id: string): Observable<Notification> {
        const url = this.projectURL + '/' + project_id + '/collaborators/' + user_id;
        return this.api.delete(url);
    }

    public deleteSecret(project_id: string, id: string): Observable<Notification> {
        const url = this.projectURL + '/' + project_id + '/secrets/' + id;
        return this.api.delete(url);
    }

    public deleteProject(project_id: string): Observable<Notification> {
        const url = this.projectURL + '/' + project_id;
        return this.api.delete(url);
    }

    public addSecret(project_id: string, ev: Secret): Observable<Notification> {
        const url = this.projectURL + '/' + project_id + '/secrets';
        const body = JSON.stringify({ name: ev.name, value: ev.value });
        return this.api.post(url, body);
    }

    public getSecrets(project_id: string): Observable<Secret> {
        const url = this.projectURL + '/' + project_id + '/secrets';

        return this.api.get(url).mergeMap((env: Secret[]) => {
            return Observable.from(env);
        });
    }
}
