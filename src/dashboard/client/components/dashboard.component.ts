import { Component, OnInit, OnDestroy} from "@angular/core";

import { Build, BuildService } from "../services/build.service";
import { UserService } from "../services/user.service";

import { Subscription } from "rxjs";

require('../img/dashboard/addNewProject.png');
require('../img/dashboard/connectRepo.png');
require('../img/dashboard/helpcenter.png');
require('../img/dashboard/uploadProject.png');
require('../img/dashboard/support.png');
require('../img/dashboard/connect_github.png');
require('../img/dashboard/connect_github_select_repo.png');
require('../img/dashboard/machine_config_infrabox_json.png');

@Component({
    selector: "dashboard",
    templateUrl: "./dashboard.component.html"
})
export class DashboardComponent implements OnInit, OnDestroy {
    private subs = new Array<Subscription>();
    private builds = new Array<Build>();

    constructor(private buildService: BuildService, private userService: UserService) {}

    public ngOnInit() {
        if (!this.userService.isLoggedIn()) {
            return;
        }

        this.subs.push(this.buildService.getBuilds().subscribe((b: Build) => {
            if (!b.commit) {
                return;
            }

            this.builds.unshift(b);
            if (this.builds.length > 10) {
                this.builds.pop();
            }
        }));
    }

    public ngOnDestroy() {
        for (let s of this.subs) {
            s.unsubscribe();
        }
    }
}
