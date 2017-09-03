import { Component } from "@angular/core";

@Component({
    selector: "compare-metrics",
    templateUrl: "./compare_metrics.component.html"
})

export class CompareMetricsComponent {
    private isEditMode: boolean;

    public ngOnInit(): void {
        this.init();

/*
        let chart_duration = window['Morris'].Line({
            element: 'chart-duration',
            data: [0,1,2,3,4,5],
            xkey: 'build_number',
            ykeys: ['tests_duration'],
            labels: ['Test Duration'],
            hideHover: 'false',
            resize: true,
            lineColors: ['#23c6c8'],
            parseTime: false,
            gridTextColor: ['black'],
            postUnits: 'ms',
            events:  ['2012-01-01', '2012-02-01', '2012-03-01'],
            eventLineColors: ['red'],
        });
*/
    }

    public changeBtnIcon() {
        this.isEditMode = !this.isEditMode;
    }

    private init() {
        this.isEditMode = false;
    }
}
