import { NgModule } from "@angular/core";
import { BrowserModule } from "@angular/platform-browser";
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { HttpModule } from "@angular/http";
import { MomentModule } from 'angular2-moment';

import { MarkdownModule } from 'angular2-markdown';
import { CookieService } from 'angular2-cookie/services/cookies.service';

import { routing } from "./app.routing";
import { DashboardComponent } from "./components/dashboard.component";
import { BuildDetailComponent } from "./components/project/build/detail.component";
import { JobDetailComponent } from "./components/project/job/detail.component";
import { JobHistoryComponent } from "./components/project/job/history.component";
import { JobListComponent } from "./components/project/job/list.component";
import { RepoListComponent } from "./components/menus/project_list.component";
import { JobStateListComponent } from "./components/menus/job_state_list.component";
import { JobStateBigComponent } from "./components/project/job/state_big.component";
import { DocumentComponent } from "./components/utils/document.component";
import { ProjectDetailComponent } from "./components/project/detail.component";
import { ProjectSettingsComponent } from "./components/project/settings.component";
import { ProjectCollaboratorsComponent } from "./components/project/collaborators.component";
import { JobStateTimelineComponent } from "./components/project/job/state_timeline.component";
import { JobStateComponent } from "./components/project/job/state.component";
import { JobDownloadsComponent } from "./components/project/job/downloads.component";
import { TestListComponent } from "./components/project/job/test_list.component";
import { JobStatsComponent } from "./components/project/job/stats.component";
import { BadgeComponent } from "./components/utils/badge.component";
import { TestStateComponent } from "./components/utils/test_state.component";
import { DurationComponent } from "./components/utils/duration.component";
import { StartDateComponent } from "./components/utils/start_date.component";
import { AddProjectComponent } from "./components/add_project.component";
import { EndDateComponent } from "./components/utils/end_date.component";
import { ConsoleComponent } from "./components/project/job/console.component";
import { AuthTokenComponent } from "./components/auth_token.component";
import { CompareConfigComponent } from "./components/compare_config.component";
import { CompareMetricsComponent } from "./components/compare_metrics.component";
import { SecretComponent } from "./components/project/secret.component";
import { InfraBoxService } from "./services/infrabox.service";
import { EventService } from "./services/event.service";
import { JobService } from "./services/job.service";
import { ConsoleService } from "./services/console.service";
import { ProjectService } from "./services/project.service";
import { LogService } from "./services/log.service";
import { BuildService } from "./services/build.service";
import { CommitService } from "./services/commit.service";
import { NotificationService } from "./services/notification.service";
import { APIService } from "./services/api.service";
import { TestService } from "./services/test.service";
import { UserService } from "./services/user.service";
import { LoginService, IsLoggedIn } from "./services/login.service";
import * as moment from "moment";

moment.locale('de-de', {
    calendar :  {
        sameDay: '[Today]',
        nextDay: '[Tomorrow]',
        nextWeek: 'dddd',
        lastDay: '[Yesterday]',
        lastWeek: 'DD/MM/YYYY',
        sameElse: 'DD/MM/YYYY'
    }
});

import { AppComponent } from "./app.component";
@NgModule({
    imports: [BrowserModule, FormsModule, routing, HttpModule,
        MomentModule, ReactiveFormsModule, MarkdownModule.forRoot(),
    ],
    declarations: [AppComponent, DashboardComponent, JobStateComponent,
        JobDetailComponent, JobHistoryComponent,
        RepoListComponent, JobStateListComponent, JobStateBigComponent,
        ProjectDetailComponent, TestListComponent,
        ConsoleComponent, ProjectSettingsComponent, ProjectCollaboratorsComponent,
        JobListComponent, BuildDetailComponent,
        JobStateTimelineComponent, EndDateComponent, DurationComponent,
        StartDateComponent, AddProjectComponent,
        CompareConfigComponent, CompareMetricsComponent,
        TestStateComponent, SecretComponent, AuthTokenComponent,
        DocumentComponent, BadgeComponent, JobStatsComponent, JobDownloadsComponent
    ],
    bootstrap: [AppComponent],
    providers: [JobService, LoginService, EventService, ConsoleService,
        ProjectService, LogService, BuildService, InfraBoxService,
        CommitService, TestService, UserService,
        NotificationService, IsLoggedIn, APIService, CookieService,
    ],
})
export class AppModule { }
