import { Component, OnInit, OnDestroy, Input } from "@angular/core";
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Subscription } from "rxjs/Subscription";
import { ActivatedRoute } from "@angular/router";

import { Job, JobService } from "../../../services/job.service";
import { ConsoleService, ConsoleOutput } from "../../../services/console.service";

class Section {
    public lines_raw = new Array<string>();
    public lines_html: SafeHtml;
    public lines_in_section = 0;
    private duration: number = 0;

    constructor(public line: number,
                private sanitizer: DomSanitizer,
                public text: string,
                public startTime: Date) { }

    public setEndTime(end: Date) {
        if (!this.startTime) {
            this.startTime = end;
        }

        const dur = (end.getTime() - this.startTime.getTime()) / 1000;
        this.duration = Math.max(Math.round(dur), 0);
    }

    public addLine(line: string) {
        line += "\n";
        this.lines_raw.push(line);

        if (this.lines_raw.length > 500) {
            this.lines_raw.splice(0, 1);
        }

        this.lines_in_section += 1;
    }

    public generateHtml() {
        let t = "";

        if (this.lines_raw.length >= 500) {
            t += "Output too large, only showing last 500 lines:\n";
        }

        for (let l of this.lines_raw) {
            t += l;
        }

        t = this.escapeHtml(t);

        const Convert = require('ansi-to-html');
        const convert = new Convert();

        this.lines_html = this.sanitizer.bypassSecurityTrustHtml(convert.toHtml(t));
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
}

@Component({
    selector: "codebox",
    templateUrl: "./console.component.html"
})
export class ConsoleComponent implements OnInit, OnDestroy {
    private subs = new Array<Subscription>();
    private job: Job;
    private linesProcessed = 1;
    private console: ConsoleOutput;
    private sections = new Array<Section>();
    private currentSection: Section;

    constructor(private consoleService: ConsoleService,
        private sanitizer: DomSanitizer,
        private route: ActivatedRoute,
        private jobService: JobService) {
        this.linesProcessed = 1;
        this.currentSection = new Section(1, this.sanitizer, "Console Output", null);
        this.sections.push(this.currentSection);
    }

    public ngOnInit(): void {
       this.subs.push(this.route.parent.params.subscribe((params) => {
            const project_id = params["project_id"];
            const job_id = params["job_id"];

            this.getJob(job_id);
        }));
    }

    public getJob(job_id: string): void {
        this.subs.push(this.jobService.getJob(job_id).subscribe((j: Job) => {
            this.job = j;
            this.getConsoleOutput();
        }));
    }

    private getTime(d: string) {
        const parts = d.split(":");
        const t = new Date();

        t.setHours(parseInt(parts[0], 10));
        t.setMinutes(parseInt(parts[1], 10));
        t.setSeconds(parseInt(parts[2], 10));

        return t;
    }

    private getConsoleOutput() {
        this.console = this.consoleService.getConsole(this.job.id);
        this.subs.push(this.console.subscribe((lines: string[]) => {
            const splitted = new Array<string>();

            for (const l of lines) {
                splitted.push.apply(splitted, l.split("\n"));
            }

            for (let line of splitted) {
                if (line === "") {
                    continue;
                }

                let header = "";
                let isSection = false;

                let idx = line.indexOf("|##");
                let date = null;

                if (idx >= 0) {
                    header = line.substr(idx + 1);
                    const d = line.substr(0, idx);
                    date = this.getTime(d);
                    isSection = true;
                }

                idx = line.indexOf("|Step");
                if (idx >= 0) {
                    header = line.substr(idx + 1);
                    const d = line.substr(0, idx);
                    date = this.getTime(d);
                    isSection = true;
                }

                if (isSection) {
                    this.currentSection.setEndTime(date);
                    this.currentSection.generateHtml();
                    this.currentSection = new Section(this.linesProcessed, this.sanitizer, header, date);
                    this.linesProcessed++;
                    this.sections.push(this.currentSection);
                } else {
                    this.currentSection.addLine(line);
                    this.linesProcessed++;
                }
            }

            this.currentSection.generateHtml();
        }));
    }

    public ngOnDestroy(): void {
        this.unsubscribe();
    }

    private unsubscribe() {
        if (!this.subs) {
            return;
        }

        for (const s of this.subs) {
            s.unsubscribe();
        }

        this.subs = new Array<Subscription>();
    }
}
