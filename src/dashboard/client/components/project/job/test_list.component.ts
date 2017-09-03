import { Component, OnInit, OnDestroy, Input } from "@angular/core";
import { Subscription } from "rxjs/Subscription";
import { ActivatedRoute } from "@angular/router";

import { Job, JobService } from "../../../services/job.service";
import { Test, TestState, TestService, TestStateList } from "../../../services/test.service";

class Measurement {
    public chart: any = null;
    constructor(public name: string, public data: any[], public unit: string) {}
}

class TestEntry {
    public test: Test;
    public show_details: boolean;
    public index: number;
    public measurements = new Array<Measurement>();

    constructor(t: Test, index: number) {
        this.test = t;
        this.show_details = false;
        this.index = index;
    }
}

@Component({
    selector: "test-list",
    templateUrl: "./test_list.component.html"
})
export class TestListComponent implements OnInit, OnDestroy {
    private subs = new Array<Subscription>();
    private job: Job;
    private tests: TestEntry[];

    // For search
    private all_tests = new Array<TestEntry>();
    private all_states: TestState[];
    private input_search: string;
    private input_states = new Map<TestState, boolean>();

    constructor(private testService: TestService,
                private jobService: JobService,
                private route: ActivatedRoute) {
        this.all_states = TestStateList;

        for (const s of this.all_states) {
            this.input_states.set(s, true);
        }
    }

    public ngOnInit(): void {
       this.subs.push(this.route.parent.params.subscribe((params) => {
            const job_id = params["job_id"];
            this.getJob(job_id);
        }));
    }

    public getJob(job_id: string): void {
        this.subs.push(this.jobService.getJob(job_id).subscribe((j: Job) => {
            this.job = j;
            this.getTests();
        }));
    }

    public getTests(): void {
        this.subs.push(this.testService.getTestRuns(this.job.project_id, this.job.id).subscribe((t: Test) => {
            if (!this.tests) {
                this.tests = new Array<TestEntry>();
            }

            const te = new TestEntry(t, this.tests.length);
            this.tests.push(te);
            this.all_tests.push(te);
        }));

        let chart_results = null;
        let chart_tests = null;

        this.subs.push(this.testService.getTestStatsHistory(this.job.project_id,
            this.job.id).subscribe((data: any) => {
                if (!data || data.length === 0) {
                    return;
                }

                const chart_duration = window['Morris'].Line({
                        element: 'chart-duration',
                        data: data,
                        xkey: 'build_number',
                        ykeys: ['tests_duration'],
                        labels: ['Test Duration'],
                        hideHover: 'false',
                        resize: true,
                        lineColors: ['#23c6c8'],
                        parseTime: false,
                        gridTextColor: ['black'],
                        postUnits: 'ms'
                });

                $('a[data-toggle="tab"]').on('shown.bs.tab', (e) => {
                    chart_duration.redraw();

                    if (!chart_results && e.target['hash'] === '#tab-chart-results')  {
                        chart_results = window['Morris'].Bar({
                            element: 'chart-results',
                            data: data,
                            xkey: 'build_number',
                            ykeys: ['tests_failed', 'tests_skipped', 'tests_passed'],
                            labels: ['failed', 'skipped', 'successful'],
                            hideHover: 'false',
                            resize: true,
                            barColors: ['#cc5965', 'dimgrey', '#1ab394'],
                            gridTextColor: ['black']
                        });
                    }

                    if (!chart_tests && e.target['hash'] === '#tab-chart-tests')  {
                        chart_tests = window['Morris'].Bar({
                            element: 'chart-tests',
                            data: data,
                            xkey: 'build_number',
                            ykeys: ['tests_added'],
                            labels: ['added'],
                            hideHover: 'false',
                            resize: true,
                            barColors: ['#cc5965'],
                            gridTextColor: ['black']
                        });
                    }
                });
            }));
    }

    public showMore(t: TestEntry) {
        t.measurements = new Array<Measurement>();

        const s = this.testService.getTestHistory(this.job.project_id,
            this.job.id, t.test.suite, t.test.name).subscribe((data: any[]) => {

                if (!data || data.length === 0) {
                    return;
                }

                const measurements = new Map<string, Measurement>();

                const result_data = [];
                for (const d of data) {
                    // Result chart
                    const r = {
                        success: 0,
                        failure: 0,
                        build_number: d.build_number
                    };

                    if (d.state === 'ok') {
                        r.success = 1;
                    } else if (d.state === 'failure' || d.state === 'error') {
                        r.failure = 1;
                    }

                    result_data.push(r);

                    // Measurements
                    for (const m of d.measurements) {
                        const new_measurement = {
                            value: m.value,
                            build_number: d.build_number
                        };

                        if (measurements.has(m.name)) {
                            const measurement = measurements.get(m.name);
                            measurement.data.push(new_measurement);
                        } else {
                            measurements.set(m.name, new Measurement(m.name, [new_measurement], m.unit));
                        }
                    }
                }

                measurements.forEach((value: Measurement, index: string, map: any) => {
                    t.measurements.push(value);
                });

                t.show_details = true;

                setTimeout(() => {
                    $('a[data-toggle="tab"]').on('shown.bs.tab', (e) => {
                        for (let i = 0; i < t.measurements.length; ++i) {
                            const m = t.measurements[i];

                            if (m.chart) {
                                continue;
                            }

                            if (e.target['hash'] === '#tab-list-' + i + '-' + t.index)  {
                                const chart_name = 'morris-test-measurement-' + i + '-' + t.index;
                                const chart_data = t.measurements[i].data;

                                m.chart =  window['Morris'].Line({
                                    element: chart_name,
                                    data: chart_data,
                                    xkey: 'build_number',
                                    ykeys: ['value'],
                                    labels: [m.unit],
                                    hideHover: 'false',
                                    resize: true,
                                    lineColors: ['#23c6c8'],
                                    parseTime: false,
                                    gridTextColor: ['black']
                                });
                            }
                        }
                    });

                    this.showLineChart('morris-test-duration-' + t.index, data);
                    this.showResultChart('morris-test-result-' + t.index, result_data);
                }, 0);
            });

        this.subs.push(s);
    }

    private showLineChart(name: string, data: any) {
        const chart = window['Morris'].Line({
            element: name,
            data: data,
            xkey: 'build_number',
            ykeys: ['duration'],
            labels: ['Test Duration'],
            hideHover: 'false',
            resize: true,
            lineColors: ['#23c6c8'],
            parseTime: false,
            gridTextColor: ['black']
        });

        $('a[data-toggle="tab"]').on('shown.bs.tab', (e) => {
            chart.redraw();
        });

        return chart;
    }

    private showResultChart(name: string, data: any) {
        for (const d of data) {
            d.failure *= -1;
        }

        const chart = window['Morris'].Bar({
            element: name,
            data: data,
            xkey: 'build_number',
            ykeys: ['failure', 'success'],
            axes: 'x',
            labels: ['failed', 'passed'],
            hideHover: 'false',
            resize: true,
            barColors: ['#cc5965', '#1ab394'],
            stacked: true,
            grid: true
        });

         $('a[data-toggle="tab"]').on('shown.bs.tab', (e) => {
            chart.redraw();
        });

        return chart;
    }

    public showLess(t: TestEntry) {
        t.show_details = false;
    }

    public ngOnDestroy(): void {
        this.unsubscribe();
    }

    public search(): void {
        this.tests = new Array<TestEntry>();

        for (const t of this.all_tests) {
            if (this.checkFilter(t.test)) {
                t.index = this.tests.length;
                this.tests.push(t);
            } else {
                t.show_details = false;
            }
        }

        return;
    }

    public change(s: TestState) {
        const state = this.input_states.get(s);
        this.input_states.set(s, !state);
    }

     public getVisibility(s: TestState) {
         const v = this.input_states.get(s);
         return v;
    }

    private checkFilter(t: Test): boolean {
        if (this.input_search && this.input_search !== "") {
            let found = false;
            if (t.name.includes(this.input_search)) {
                found = true;
            }

            if (t.suite.includes(this.input_search)) {
                found = true;
            }

            if (!found) {
                return false;
            }
        }

        if (!this.input_states.get(t.state)) {
            return false;
        }

        return true;
    }

    private unsubscribe() {
        for (const s of this.subs) {
            s.unsubscribe();
        }

        this.subs = new Array<Subscription>();
    }
}
