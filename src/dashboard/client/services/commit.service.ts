import { Injectable } from "@angular/core";
import { Observable } from "rxjs/Observable";
import { APIService } from "./api.service";

import "rxjs/add/operator/map";

export class Commit {
    public id: string;
    public message: string;
    public author_name: string;
    public author_email: string;
    public author_username: string;
    public committer_name: string;
    public committer_email: string;
    public committer_username: string;
    public committer_avatar_url: string;
    public url: string;
    public branch: string;
    public tag: string;
}

@Injectable()
export class CommitService {
    private commits = new Map<string, Commit>();

    constructor(private api: APIService) {}

    public getCommit(project_id: string, commit_id: string): Observable<Commit> {
        const url = "api/dashboard/project/" + project_id + "/commit/" + commit_id;
        return this.api.get(url);
    }

    public getOrCreateCommitFromEvent(event: any): Commit {
        const project_id = event.project.id as string;
        const c = event.commit as Commit;
        const id = project_id + c.id;
        if (this.commits.has(id)) {
            return this.commits.get(id);
        } else {
            this.commits.set(id, c);
            return c;
        }
    }
}
