import { Component, OnInit, OnDestroy, Input, AfterViewInit } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

import { Subscription } from "rxjs";
import { Observable } from "rxjs/Observable";

import { Job, Tab, JobService } from "../../services/job.service";

class DonutChart {
    private chart: any = null;

    constructor(private config: any) {}

    public redraw() {
        if (!$(this.config.element)) {
            return;
        }

        if (!this.chart) {
            this.chart = window['Morris'].Donut(this.config);
        }

        this.chart.redraw();
    }
}

@Component({
    selector: "infrabox-document",
    template: `<div [innerHTML]="content"></div>`,
})
export class DocumentComponent implements OnInit, OnDestroy {
    private sub: Subscription;
    private job: Job;
    private content: SafeHtml;
    private charts = new Array<any>();
    private name: string;

    constructor(private sanitizer: DomSanitizer,
                private jobService: JobService,
                private route: ActivatedRoute) {}

    public ngOnInit(): void {
        let job_id = null;
        let project_id = null;
        this.sub = this.route.parent.params.flatMap((params) => {
            job_id = params["job_id"];
            project_id = params["project_id"];
            return this.route.params;
        }).flatMap((p) => {
            this.name = p["document_name"];
            return this.jobService.getTabs(project_id, job_id);
        }).subscribe((tabs: Tab[]) => {
            for (const t of tabs) {
                const name = t.name.replace('.', '_').replace(' ', '_');
                if (name === this.name) {
                    this.content = this.sanitizer.bypassSecurityTrustHtml(
                        this.createHTML(JSON.parse(t.data)));
                    break;
                }
            }

            this.showCharts();
        });
    }

    public ngOnDestroy(): void {
        if (this.sub) {
            this.sub.unsubscribe();
        }
    }

    public showCharts() {
        setTimeout(() => {
            for (const c of this.charts) {
                c.redraw();
            }
        }, 100);
    }

    private escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };

        return text.replace(/[&<>"']/g, (m) => map[m] );
    }

    private handleString(str) {
        return this.escapeHtml(str);
    }

    private handleGrid(t) {
        let s = "<div>";
        for (const r of t.rows) {
            s += "<div class='row custom-grid'>";

            const colCount = r.length;
            const colWidth = Math.round(12 / colCount);

            for (const c of r) {
                s += "<div class='col-lg-" + colWidth + "'>";
                s += this.handleElement(c);
                s += "</div>";
            }

            s += "</div>";
        }

        s += "</div>";
        return s;
    }

    private handleTable(t) {
        let s = "<table class='custom-box'>";

        if (t.headers) {
            s += "<thead class='custom-box'><tr>";
            for (const h of t.headers) {
                s += "<th class='custom-box'>";
                s += this.handleElement(h);
                s += "</th>";
            }
            s += "</tr></thead>";
        }

        s += "<tbody class='custom-box'>";

        for (const r of t.rows) {
            s += "<tr class='custom-box'>";

            for (const c of r) {
                s += "<td class='custom-box'>";
                s += this.handleElement(c);
                s += "</td>";
            }

            s += "</tr>";
        }

        s += "</tbody>";
        s += "</table>";
        return s;
    }

    private handlePieChart(p) {
        const d = {
            element: "pie-" + p.name,
            data: [],
            resize: true,
            colors: []
        };

        for (const v of p.data) {
            d.data.push({ label: v.label, value: v.value });
            d.colors.push(this.getColor(v.color));
        }

        this.charts.push(new DonutChart(d));

        return '<div class="center-block" style="height:250px; width:250px" id="pie-' + p.name + '"></div>';
    }

    private handleParagraph(p) {
        let s = "<p class='custom-box'>";
        s += this.handleElementList(p.elements);
        s += "</p>";
        return s;
    }

    private handleIcon(i) {
        const color = this.getColor(i.color);
        let s = '<i class="fa ';
        s += i.name;
        s += '" style="color:';
        s += color;
        s += '"aria-hidden="true"></i>';
        return s;
    }

    private getColor(c) {
        if (!c) {
            return null;
        }

        switch (c) {
            case "red":
                return "#cc5965";
            case "yellow":
                return "#ffeb3b";
            case "blue":
                return "#23c6c8";
            case "white":
                return c;
            case "black":
                return c;
            case "green":
                return "#1ab394";
            case "orange":
                return "#f8ac59";
            case "grey":
                return "#696969";

            default:
                return null;

        }
    }

    private handleText(txt) {
        let s = "";

        let emph = null;
        switch (txt.emphasis) {
            case "bold":
                emph = "strong";
                break;
            case "italic":
                emph = "em";
                break;
            default:
                emph = null;
        }

        if (emph) {
            s += "<" + emph + ">";
        }

        const color = this.getColor(txt.color);
        if (color) {
            s += "<font color=\"" + color + "\">";
        }

        s += txt.text;

        if (color) {
            s += "</font>";
        }

        if (emph) {
            s += "</" + emph + ">";
        }

        s += "\n";
        return s;
    }

    private handleUnorderedList(elem) {
        let s = "<ul class='custom-box'>";

        for (const e of elem.elements) {
            let addli = false;
            if (e.type !== "ordered_list" && e.type !== "unordered_list") {
                addli = true;
            }

            if (addli) {
                s += "<li class='custom-box'>";
            }

            s += this.handleElement(e);

            if (addli) {
                s += "</li>";
            }
        }

        s += "</ul>";
        return s;
    }

    private handleOrderedList(elem) {
        let s = "<ol class='custom-box'>";

        for (const e of elem.elements) {
            s += "<li class='custom-box'>" + this.handleElement(e) + "</li>";
        }

        s += "</ol>";
        return s;
    }

    private handleElement(elem) {
        switch (elem.type) {
            case "h1":
                return "<h1 class='custom-box'><i class='fa fa-cubes'></i>" + this.handleString(elem.text) + "</h1>\n";
            case "h2":
                return "<h2 class='custom-box'><i class='fa fa-cube'></i> " + this.handleString(elem.text) + "</h2>\n";
            case "h3":
                return "<h3 class='custom-box'>" + this.handleString(elem.text) + "</h3>\n";
            case "h4":
                return "<h4 class='custom-box'>" + this.handleString(elem.text) + "</h4>\n";
            case "h5":
                return "<h5 class='custom-box'>" + this.handleString(elem.text) + "</h5>\n";
            case "code":
                return "<pre class='custom-box'>" + this.handleString(elem.text) + "</pre>\n";
            case "group":
                return this.handleElementList(elem.elements);
            case "hline":
                return "<hr/>\n";
            case "paragraph":
                return this.handleParagraph(elem);
            case "icon":
                return this.handleIcon(elem);
            case "text":
                return this.handleText(elem);
            case "pie":
                return this.handlePieChart(elem);
            case "table":
                return this.handleTable(elem);
            case "grid":
                return this.handleGrid(elem);
            case "unordered_list":
                return this.handleUnorderedList(elem);
            case "ordered_list":
                return this.handleOrderedList(elem);
            default:
                return "";
        }
    }

    private handleElementList(list) {
        let s = "";
        for (const e of list) {
            s += this.handleElement(e);
        }

        return s;
    }

    private createHTML(data) {
        return this.handleElementList(data.elements);
    }
}
