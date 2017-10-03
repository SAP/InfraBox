import { Component, Input, OnInit } from "@angular/core";
import { SimpleChanges, OnChanges } from "@angular/core/index";
import { Subscription } from "rxjs";
import { Observable } from "rxjs/Observable";

@Component({
    selector: "badge",
    template: `
<button data-toggle="modal" [attr.data-target]="'#' + id" type="button"
    class="btn btn-outline no-padding" style="height:20px">
        <i class="fa fa-file-code-o"></i>
</button>

<img src="https://img.shields.io/badge/{{ subject }}-{{ statusEncoded }}-{{ color }}.svg" height="20px" />

<div id="{{ id }}" class="modal fade" aria-hidden="true">
    <div class="modal-dialog" style="width:50%">
        <div class="modal-content">
            <div class="modal-body">
                <div class="m-t-md m-b-lg">
                    <h2>Embed your badge</h2>
                </div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        Markdown
                    </div>
                    <div class="panel-body">
                        <![CDATA[[![{{ subject }}]({{ url }})]({{ link }})]]>
                    </div>
                </div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        HTML
                    </div>
                    <div class="panel-body">
                        <![CDATA[<a href="{{ link }}"><img src="{{ url }}" alt="{{ subject }}"/></a>]]>
                    </div>

                </div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        RST
                    </div>
                    <div class="panel-body">
                        <![CDATA[.. image:: {{ url }} :target: {{ link }}]]>
                    </div>
                </div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        Textile
                    </div>
                    <div class="panel-body">
                        <![CDATA[!{{ url }}({{ subject }})!:{{ link }}]]>
                    </div>
                </div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        RDOC
                    </div>
                    <div class="panel-body">
                        <![CDATA[{<img src="{{ url }}" alt="{{ subject }}"/>}[{{ link }}]]]>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
`,
})
export class BadgeComponent implements OnInit, OnChanges {
    @Input() private subject: string;
    @Input() private status: string;
    @Input() private color: string;
    @Input() private project_id: string;
    @Input() private job_name: string;
    private api_host: string;
    private dashboard_host: string;
    private id: string;
    private url: string;
    private link: string;
    private statusEncoded: string;

    constructor() {
        this.api_host = window['INFRABOX_API_URL'];
        this.dashboard_host = window['INFRABOX_DASHBOARD_URL'];
    }

    public ngOnInit() {
        this.init();
    }

    public ngOnChanges(changes: SimpleChanges) {
        this.init();
    }

    private init() {
        this.statusEncoded = encodeURI(this.status);
        this.id = `badge-${this.subject}-${this.status}`;
        this.id = this.id.replace(/\W+/g, "");
        this.url = `${this.api_host}/v1/project/${this.project_id}/badge.svg?subject=${this.subject}&job_name=${this.job_name}`;
        this.url = encodeURI(this.url);
        this.link = `${this.dashboard_host}/dashboard/project/${this.project_id}`;
    }
}
