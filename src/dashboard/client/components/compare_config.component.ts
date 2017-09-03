import { Component, OnInit, OnDestroy, Input } from "@angular/core";
import { Subscription } from "rxjs/Subscription";
import { Job } from "../services/job.service";
import { Build, BuildService } from "../services/build.service";
import { Test, TestService } from "../services/test.service";
import { ActivatedRoute } from "@angular/router";

@Component({
    selector: "compare-config",
    templateUrl: "./compare_config.component.html"
})

export class CompareConfigComponent implements OnInit, OnDestroy {
    @Input() private job: Job;
    private build: Build;
    private metricsList: MetricInfo[];
    private subs: Subscription[];
    private jobsWithTestSuites: Map<string, JobsWithTestSuites>;
    private testsOfSuites: Map<string, TestSuite>;

    constructor(private route: ActivatedRoute,
        private buildService: BuildService,
        private testService: TestService) {
    }

    public ngOnInit(): void {
        this.route.params.subscribe((params) => {
            this.init();
            let sub = this.buildService.getBuild(this.job.project_id, this.job.build.id).subscribe((b: Build) => {
                this.build = b;
            });
            this.subs.push(sub);
        });

/*
        let firstMetric = new MetricInfo("noJob", "noTestSuite", "noTest", "noMetric");
        this.metricsList.push(firstMetric);
        this.setJobsWithTests(this.build);
        */
    }

    public ngOnDestroy(): void {
        this.unsubscribe();
    }

    public addMetric() {
        let newMetric = new MetricInfo("noJob", "noTestSuite", "noTest", "noMetric");
        this.metricsList.push(newMetric);
    }

    public deleteMetric(metricId: number) {
        this.metricsList.splice(metricId, 1);
    }

    public setSelectedJob(selected: string, id: number) {
        let newMetric = this.metricsList[id];
        newMetric.mJob = selected;

        for (let j of this.build.jobs) {
            if (j.name !== selected) {
                continue;
            }
            newMetric.mTestSuites = new Array<string>();
            newMetric.mTestSuites = this.jobsWithTestSuites.get(selected).suites;
        }
        this.setSelectedSuite(newMetric.mTestSuites[0], id);
    }

    public setSelectedSuite(selected: string, id: number) {
        let newMetric = this.metricsList[id];
            newMetric.mTestSuite = selected;

            for (let t of newMetric.mTestSuites) {
                if (t !== selected) {
                    continue;
                }
                newMetric.mTests = new Array<Test>();
                newMetric.mTests = this.testsOfSuites.get(selected).tests;
            }
    }

    public setColor(selected: string, id: number) {
        let newMetric = this.metricsList[id];
        newMetric.mColor = selected;
    }

    public setJobsWithTests(b: Build) {
        for (let j of this.build.jobs) {
            let jobSuites = new Array<string>();
            this.subs.push(this.testService.getTestRuns(j.project_id, j.id).subscribe((t: Test) => {
                if (this.jobsWithTestSuites.has(j.name)) {
                    jobSuites = this.jobsWithTestSuites.get(j.name).suites;
                    if (jobSuites.indexOf(t.suite) < 0) {
                        jobSuites.push(t.suite);
                    }
                    this.setTestsForSuites(t);
                } else {
                    let jobSuites = new Array<string>();
                    jobSuites.push(t.suite);
                    let jmap = new JobsWithTestSuites(j.name);
                    jmap.suites = jobSuites;
                    this.jobsWithTestSuites.set(j.name, jmap);
                    this.setTestsForSuites(t);
                }
            }));
        }
    }

    public setTestsForSuites(t: Test) {
        if (this.testsOfSuites.has(t.suite)) {
            this.testsOfSuites.get(t.suite).tests.push(t);
        } else {
            let suiteTests = new Array<Test>();
            suiteTests.push(t);
            let tmap = new TestSuite(t.suite);
            tmap.tests = suiteTests;
            this.testsOfSuites.set(t.suite, tmap);
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

    private init() {
        this.metricsList = new Array<MetricInfo>();
        this.subs = new Array<Subscription>();
        this.jobsWithTestSuites = new Map<string, JobsWithTestSuites>();
        let jwtsTemp = new JobsWithTestSuites("");
        this.jobsWithTestSuites.set("", jwtsTemp);
        let tsTemp = new TestSuite("");
        this.testsOfSuites = new Map<string, TestSuite>();
        this.testsOfSuites.set("", tsTemp);
    }
}

class TestSuite {
    public name: string;
    public tests = new Array<Test>();

    constructor(name: string) {
        this.name = name;
    }
}

class JobsWithTestSuites {
    public name: string;
    public suites = new Array<string>();

    constructor(name: string) {
        this.name = name;
    }
}

class MetricInfo {
    public mJob: string;
    public mTestSuite: string;
    public mTest: string;
    public mMetric: string;
    public mSuites: Map<string, TestSuite>;
    public mTests: Test[];
    public mTestSuites: string[];
    public mColor: string;

    constructor(iJob: string, iTestSuite: string, iTest: string, iMetric: string) {
        this.mJob = iJob;
        this.mTestSuite = iTestSuite;
        this.mTest = iTest;
        this.mMetric = iMetric;
    }
}

class TestEntry {
    public test: Test;
    public show_details: boolean;
    public index: number;

    constructor(t: Test, index: number) {
        this.test = t;
        this.show_details = false;
        this.index = index;
    }
}
