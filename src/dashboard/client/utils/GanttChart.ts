import { Router } from "@angular/router";
import { Job, Dependency } from "../services/job.service";

import * as Raphael from 'raphael';

class StateFormat {
    public stateIcon: string;
    public stateColor: string;

    constructor(
        private jobState: string) {
        this.setFormat(jobState);
    }

    private setFormat(js: string) {
        if (js === 'running') {
            this.stateIcon = '\uf192';
            this.stateColor = "#23c6c8";
        } else if (js === 'failure') {
            this.stateIcon = '\uf0e7';
            this.stateColor = "#cc5965";
        } else if (js === 'error') {
            this.stateIcon = '\uf1e2';
            this.stateColor = "black";
        } else if (js === 'queued') {
            this.stateIcon = '\uf04c';
            this.stateColor = "lightgrey";
        } else if (js === 'scheduled') {
            this.stateIcon = '\uf03a';
            this.stateColor = "dimgrey";
        } else if (js === 'finished') {
            this.stateIcon = '\uf00c';
            this.stateColor = "#1ab394";
        } else if (js === 'killed') {
            this.stateIcon = '\uf05e';
            this.stateColor = "dimgrey";
        } else if (js === 'skipped') {
            this.stateIcon = '\uf050';
            this.stateColor = "dimgrey";
        }
    }
}

/* tslint:disable */
(function() {
    let tokenRegex = /\{([^\}]+)\}/g,
        objNotationRegex = /(?:(?:^|\.)(.+?)(?=\[|\.|$|\()|\[('|")(.+?)\2\])(\(\))?/g, // matches .xxxxx or ["xxxxx"] to run over object properties
        replacer = function(all, key, obj) {
            let res = obj;
            key.replace(objNotationRegex, function(all, name, quote, quotedName, isFunc) {
                name = name || quotedName;
                if (res) {
                    if (name in res) {
                        res = res[name];
                    }
                    typeof res == "function" && isFunc && (res = res());
                }
            });
            res = (res == null || res == obj ? all : res) + "";
            return res;
        },
        fill = function(str, obj) {
            return String(str).replace(tokenRegex, function(all, key) {
                return replacer(all, key, obj);
            });
        };
    Raphael.fn.popup = function(X, Y, set, pos, ret) {
        pos = String(pos || "top-middle").split("-");
        pos[1] = pos[1] || "middle";
        let r = 5,
            bb = set.getBBox(),
            w = Math.round(bb.width),
            h = Math.round(bb.height),
            x = Math.round(bb.x) - r,
            y = Math.round(bb.y) - r,
            gap = Math.min(h / 2, w / 2, 10),
            shapes = {
                top: "M{x},{y}h{w4},{w4},{w4},{w4}a{r},{r},0,0,1,{r},{r}v{h4},{h4},{h4},{h4}a{r},{r},0,0,1,-{r},{r}l-{right},0-{gap},{gap}-{gap}-{gap}-{left},0a{r},{r},0,0,1-{r}-{r}v-{h4}-{h4}-{h4}-{h4}a{r},{r},0,0,1,{r}-{r}z",
                bottom: "M{x},{y}l{left},0,{gap}-{gap},{gap},{gap},{right},0a{r},{r},0,0,1,{r},{r}v{h4},{h4},{h4},{h4}a{r},{r},0,0,1,-{r},{r}h-{w4}-{w4}-{w4}-{w4}a{r},{r},0,0,1-{r}-{r}v-{h4}-{h4}-{h4}-{h4}a{r},{r},0,0,1,{r}-{r}z",
                right: "M{x},{y}h{w4},{w4},{w4},{w4}a{r},{r},0,0,1,{r},{r}v{h4},{h4},{h4},{h4}a{r},{r},0,0,1,-{r},{r}h-{w4}-{w4}-{w4}-{w4}a{r},{r},0,0,1-{r}-{r}l0-{bottom}-{gap}-{gap},{gap}-{gap},0-{top}a{r},{r},0,0,1,{r}-{r}z",
                left: "M{x},{y}h{w4},{w4},{w4},{w4}a{r},{r},0,0,1,{r},{r}l0,{top},{gap},{gap}-{gap},{gap},0,{bottom}a{r},{r},0,0,1,-{r},{r}h-{w4}-{w4}-{w4}-{w4}a{r},{r},0,0,1-{r}-{r}v-{h4}-{h4}-{h4}-{h4}a{r},{r},0,0,1,{r}-{r}z"
            },
            offset = {
                hx0: X - (x + r + w - gap * 2),
                hx1: X - (x + r + w / 2 - gap),
                hx2: X - (x + r + gap),
                vhy: Y - (y + r + h + r + gap),
                "^hy": Y - (y - gap)

            },
            mask = [{
                x: x + r,
                y: y,
                w: w,
                w4: w / 4,
                h4: h / 4,
                right: 0,
                left: w - gap * 2,
                bottom: 0,
                top: h - gap * 2,
                r: r,
                h: h,
                gap: gap
            }, {
                x: x + r,
                y: y,
                w: w,
                w4: w / 4,
                h4: h / 4,
                left: w / 2 - gap,
                right: w / 2 - gap,
                top: h / 2 - gap,
                bottom: h / 2 - gap,
                r: r,
                h: h,
                gap: gap
            }, {
                x: x + r,
                y: y,
                w: w,
                w4: w / 4,
                h4: h / 4,
                left: 0,
                right: w - gap * 2,
                top: 0,
                bottom: h - gap * 2,
                r: r,
                h: h,
                gap: gap
            }][2] //[pos[1] == "middle" ? 1 : (pos[1] == "top" || pos[1] == "left") * 2];
        let dx = 0,
            dy = 0,
            out = this.path(fill(shapes[pos[0]], mask)).insertBefore(set);
        switch (pos[0]) {
            case "top":
                dx = X - (x + r + mask.left + gap);
                dy = Y - (y + r + h + r + gap);
                break;
            case "bottom":
                dx = X - (x + r + mask.left + gap);
                dy = Y - (y - gap);
                break;
            case "left":
                dx = X - (x + r + w + r + gap);
                dy = Y - (y + r + mask.top + gap);
                break;
            case "right":
                dx = X - (x - gap);
                dy = Y - (y + r + mask.top + gap);
                break;
        }
        out.translate(dx, dy);
        if (ret) {
            ret = out.attr("path");
            out.remove();
            return {
                path: ret,
                dx: dx,
                dy: dy
            };
        }
        set.translate(dx, dy);
        return out;
    };
})();

/* tslint:enable */

class GanttJob {
    public x: number;
    public y: number;
    public text: any;
    public shape: any;
    public parentElements = new Array<any>();
    public pos: number;

    constructor(
        public id: string,
        public name: string,
        public dependencies: Dependency[],
        public level: number,
        public state: string,
        public project_id: string,
        public build_id: string) { }
}

export class GanttChart {
    private jobs = new Array<GanttJob>();
    private box_width = 30;
    private box_height = 30;
    private box_padding = 10;
    private line_width = 2;
    private r: RaphaelPaper;
    private frame: any;
    private label: any;
    private labelOffset = 0;
    private maxChain = 0;
    private label_visible = true;
    private symbolSize = 0;
    private router: Router;
    private svg_width = 0;

    constructor(router: Router) {
        this.router = router;
        this.symbolSize = this.box_height * 0.7;
        if (this.box_width <= this.box_height) {
            this.symbolSize = this.box_width * 0.7;
        }
    }

    public setJobs(jobs: Job[]) {
        this.jobs = [];

        for (const j of jobs) {
            this.addJob(j);
        }

        this.createRaphael();
    }

    private createRaphael() {
        const height = this.jobs.length * (this.box_height + this.box_padding) + this.box_padding;
        if (document.getElementById("tab-content")) {
            this.svg_width = document.getElementById("tab-content").offsetWidth;
        }

        if (this.r) {
            this.r.clear();
            $("#holder").empty();
        }

        this.r = Raphael("holder", this.svg_width, height);
    }

    public updateJob(job: Job) {
        if (!this.r) {
            return;
        }

        for (const j of this.jobs) {
            if (j.id === job.id) {
                j.state = job.getStateValue();
                this.setNodeAttributes(j);
            }
        }
    }

    private findJobPosById(id: string) {
        for (let i = 0; i < this.jobs.length; ++i) {
            if (this.jobs[i].id === id) {
                return i;
            }
        }

        return null;
    }

    private allParentsAvailable(job: GanttJob) {
        for (const dep of job.dependencies) {
            const r = this.findJobPosById(dep['job-id']);
            if (r === null) {
                return false;
            }
        }

        return true;
    }

    private addJob(j: Job) {
        const job = new GanttJob(j.id, j.name, j.dependencies, 0, j.getStateValue(), j.project_id, j.build.id);
        this.jobs.push(job);
    }

    private sortJobs() {
        const all_jobs = this.jobs;
        this.jobs = [];

        // Find Start
        for (let i = 0; i < all_jobs.length; ++i) {
            const job = all_jobs[i];
            if (!job.dependencies || !job.dependencies.length) {
                this.jobs.push(job);
                all_jobs.splice(i, 1);
                break;
            }
        }

        let updated = true;
        while (updated) {
            updated = false;

            let parent_i = this.jobs.length;
            while (parent_i--) {
                const parent = this.jobs[parent_i];

                for (let i = 0; i < all_jobs.length; ++i) {
                    const job = all_jobs[i];
                    let found_all_deps = true;
                    let found_parent = false;

                    for (const dep of job.dependencies) {
                        const r = this.findJobPosById(dep['job-id']);
                        if (r === null) {
                            found_all_deps = false;
                        }

                        if (dep['job-id'] === parent.id) {
                            found_parent = true;
                        }
                    }

                    if (found_all_deps && found_parent) {
                        this.jobs.push(job);
                        all_jobs.splice(i, 1);
                        updated = true;
                        break;
                    }
                }

                if (updated) {
                    break;
                }
            }
        }

        for (const j of all_jobs) {
            this.jobs.push(j);
        }

        for (let i = 0; i < this.jobs.length; ++i) {
            const job = this.jobs[i];
            job.level = this.countParents(job);
            job.pos = i;
        }
    }

    private getX(job) {
        return (job.level * this.box_width) + (job.level * this.box_padding);
    }

    private getY(job) {
        return (job.pos * this.box_height) + (job.pos * this.box_padding) + (this.box_padding / 2);
    }

    private getParent(dep: Dependency) {
        for (const job of this.jobs) {
            if (job.id === dep['job-id']) {
                return job;
            }
        }

        return null;
    }

    private countParents(job: GanttJob) {
        if (job.dependencies.length === 0) {
            return 0;
        } else {
            let c = 0;
            for (const dep of job.dependencies) {
                for (const j of this.jobs) {
                    if (j.id !== dep['job-id']) {
                        continue;
                    }

                    const r = this.countParents(j) + 1;

                    if (r > c) {
                        c = r;

                        if (r > this.maxChain) {
                            this.maxChain = r;
                        }
                    }
                }
            }

            return c;
        }
    }

    private createNode(x: number, y: number, job: GanttJob) {
        const s = this.r.rect(x, y, this.box_width, this.box_height, 2);
        job.shape = s;
        job.x = x;
        job.y = y;

        if (this.label_visible) {
            const jobLabel = this.r.text(0, job.y + this.box_height / 2, job.name);
            jobLabel.attr({
                "font": '13px Helvetica, Arial',
                "font-weight": "bold",
                "fill": "#676a6c",
                "cursor": "pointer"
            });

            jobLabel.click(() => {
                this.router.navigate(["/dashboard", "project", job.project_id, "build", job.build_id, "job", job.id]);
            });

            const labelLength = jobLabel.getBBox().width;
            jobLabel["translate"](labelLength / 2 + 15, 0);
        }

        this.setNodeAttributes(job);

        s.click(() => {
            this.router.navigate(["/dashboard", "project", job.project_id, "build", job.build_id, "job", job.id]);
        });

        const hoverEnter = () => {
            if (this.frame) {
                this.frame.hide();
            }

            if (job.x + this.box_width < this.r.width - 2 * this.box_padding) {
                this.frame = this.r['popup'](job.x + this.box_width, job.y +
                    (this.box_height / 2), this.label, "right");
                this.frame.attr({
                    "fill": "white",
                    "stroke": "#666",
                    "stroke-width": 1,
                    "fill-opacity": 0.6
                });
            } else {
                this.frame = this.r['popup'](job.x, job.y + (this.box_height / 2), this.label, "left");
                this.frame.attr({
                    "fill": "white",
                    "stroke": "#666",
                    "stroke-width": 1,
                    "fill-opacity": 1
                });
            }

            this.label[0].attr({
                "text": job.name,
                "fill": "#676a6c",
                "font-weight": "bold"
            }).show();

            this.label[1].attr({
                text: "State: " + job.state,
                fill: "#676a6c"
            }).show();

            for (const e of job.parentElements) {
                if (!e.g) {
                    e.g = e.glow({ color: "red", width: 2 });
                }
            }
        };

        const hoverExit = () => {
            for (const e of job.parentElements) {
                if (e.g) {
                    e.g.remove();
                    e.g = null;
                }
            }
        };

        s.hover(hoverEnter, hoverExit);
    }

    private setNodeAttributes(job: GanttJob) {
        const nodeState = new StateFormat(job.state);

        const x = job.x + this.box_width / 2;
        const y = job.y + this.box_height / 2;

        if (job.text) {
            job.text.remove();
        }

        job.text = this.r.text(x, y, nodeState.stateIcon);
        job.text.attr({
            "font-family": "FontAwesome",
            "font-size": this.symbolSize,
            "fill": "white",
            "cursor": "pointer"
        });

        job.text.hover(() => {
            for (const e of job.parentElements) {
                if (!e.g) {
                    e.g = e.glow({ color: "red", width: 2 });
                }
            }
        }, () => {
            for (const e of job.parentElements) {
                if (e.g) {
                    e.g.remove();
                    e.g = null;
                }
            }
        });

        job.shape.attr({
            "fill": nodeState.stateColor,
            "stroke-width": 0,
            "cursor": "pointer"
        });
    }

    public draw() {
        this.sortJobs();
        const color = Raphael.getColor();

        // calculate label offset
        for (const job of this.jobs) {
            const l = this.r.text(0, 0, job.name)
                .attr({
                    "font": '13px Helvetica, Arial',
                    "font-weight": "bold",
                    "fill": "#676a6c"
                });
            const width = l.getBBox().width;
            l.hide();

            if (width > this.labelOffset) {
                this.labelOffset = width + this.box_padding + this.box_width;
            }
        }

        if (this.maxChain !== 0) {
            this.box_width =
                (this.svg_width - this.labelOffset -
                    (this.maxChain + 2) * this.box_padding) / (this.maxChain + 1);

            if (this.box_width <= 15) {
                this.labelOffset = 10;
                this.box_width = 15;
                this.label_visible = false;
            } else if (this.box_width >= 150) {
                this.box_width = 150;
                this.label_visible = true;
            } else {
                this.label_visible = true;
            }
        }

        // draw nodes
        for (const job of this.jobs) {
            const x = this.getX(job) + this.labelOffset;
            const y = this.getY(job);
            this.createNode(x, y, job);
        }

        for (const job of this.jobs) {
            job.level = this.countParents(job);

            for (const dep of job.dependencies) {
                const parent = this.getParent(dep);

                if (!parent) {
                    continue;
                }

                job.parentElements.push(parent.shape);
                for (const e of parent.parentElements) {
                    job.parentElements.push(e);
                }

                // Vertical line
                let x = this.getX(parent) + this.labelOffset +
                    (this.box_width / 2) - (this.line_width / 2);
                let y = this.getY(parent) + this.box_height;
                const h = ((this.box_height + this.box_padding) * (job.pos - parent.pos - 1))
                    + (this.box_height / 2) + this.box_padding;
                let s = this.r.rect(x, y, this.line_width, h);
                s.attr({ "fill": '#293846', "stroke-width": 0 });
                s.toBack();
                job.parentElements.push(s);

                // Horizontal line
                y = y + h;
                x = x;
                const w = (this.box_width / 2 + this.box_padding + 2) +
                    (this.box_width + this.box_padding) * (job.level - parent.level - 1);
                s = this.r.rect(x, y, w, this.line_width);
                s.attr({ "fill": '#293846', "stroke-width": 0 });
                s.toBack();
                job.parentElements.push(s);

                // draw circle
                const c = this.r.circle(x + w, y + this.line_width / 2, 5);
                c.attr({ "fill": '#293846', "stroke-width": 0 });
                job.parentElements.push(c);
                c.toBack();
            }
        }

        // Draw background table
        for (let i = 0; i < this.jobs.length; i++) {
            if ((i % 2) === 0) {
                const job = this.jobs[i];
                const s = this.r.rect(0,
                    this.getY(job) - (this.box_padding / 2), this.svg_width,
                    this.box_height + this.box_padding);
                s.attr({ "fill": '#f5f5f5', "stroke-width": 0 });
                s.toBack();
            }
        }

        this.label = this.r.set();
        const txt = { fill: "#fff" };
        const txt1 = { fill: "#fff" };
        this.label.push(this.r.text(60, 12, "InfraBox").attr(txt));
        this.label.push(this.r.text(60, 27, "InfraBox").attr(txt1).attr({ fill: color }));
        this.label.hide();
    }
}
