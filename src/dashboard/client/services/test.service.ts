import { APIService } from "./api.service";
import { Injectable } from "@angular/core";
import { Observable } from "rxjs/Observable";

export type TestState = "ok" | "failure" | "error" | "skipped";
export let TestStateList: TestState[] = ["ok", "failure", "error", "skipped"];

export class Test {
    public name: string;
    public suite: string;
    public state: TestState;
    public duration: number;
}

@Injectable()
export class TestService {
    constructor(private api: APIService) {}

    public getTestRuns(project_id: string, job_id: string): Observable<Test> {
        const url = "/api/dashboard/project/" + project_id + "/job/" + job_id + "/testruns";

        return this.api.get(url).mergeMap((tests: Test[]) => {
            return Observable.from(tests);
        });
    }

    public getTestHistory(project_id: string, job_id: string, suite: string, test: string): Observable<any> {
        const url = "/api/dashboard/project/" + project_id + "/job/" + job_id +
            "/test/history?suite=" + encodeURIComponent(suite) +
            '&test=' + encodeURIComponent(test);
        return this.api.get(url);
    }

    public getTestStatsHistory(project_id: string, job_id: string): Observable<any> {
        const url = "/api/dashboard/project/" + project_id + "/job/" + job_id + "/stats/history";
        return this.api.get(url);
    }
}
