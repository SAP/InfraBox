import { Injectable } from "@angular/core";

declare var INFRABOX_DOCS_URL: string;
declare var INFRABOX_GITHUB_ENABLED: boolean;

@Injectable()
export class InfraBoxService {
    public isGithubEnabled(): boolean {
        return INFRABOX_GITHUB_ENABLED;
    }

    public openDocs() {
        window.open(INFRABOX_DOCS_URL, "_self");
    }
}
