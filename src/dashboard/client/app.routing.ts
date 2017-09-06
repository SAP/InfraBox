import { ModuleWithProviders } from "@angular/core";
import { Routes, RouterModule } from "@angular/router";

import { ProjectDetailComponent } from "./components/project/detail.component";
import { BuildDetailComponent } from "./components/project/build/detail.component";
import { JobDetailComponent } from "./components/project/job/detail.component";
import { ConsoleComponent } from "./components/project/job/console.component";
import { JobHistoryComponent } from "./components/project/job/history.component";
import { JobStatsComponent } from "./components/project/job/stats.component";
import { JobDownloadsComponent } from "./components/project/job/downloads.component";
import { TestListComponent } from "./components/project/job/test_list.component";
import { DocumentComponent } from "./components/utils/document.component";

import { DashboardComponent } from "./components/dashboard.component";
import { ProjectSettingsComponent } from "./components/project/settings.component";
import { AddProjectComponent } from "./components/add_project.component";
import { AuthTokenComponent } from "./components/auth_token.component";
import { IsLoggedIn } from "./services/login.service";

const appRoutes: Routes = [{
    path: "",
    redirectTo: "/dashboard/start",
    pathMatch: "full"
}, {
    path: "dashboard/start",
    component: DashboardComponent
}, {
    path: "dashboard/account/project/add",
    canActivate: [IsLoggedIn],
    component: AddProjectComponent
}, {
    path: "dashboard/account/tokens",
    canActivate: [IsLoggedIn],
    component: AuthTokenComponent
}, {
    path: "dashboard/project/:project_id",
    component: ProjectDetailComponent
}, {
    path: "dashboard/project/:project_id/settings",
    canActivate: [IsLoggedIn],
    component: ProjectSettingsComponent
}, {
    path: "dashboard/project/:project_id/build/:build_id/job/:job_id",
    component: JobDetailComponent,
    children: [
        { path: '', redirectTo: 'console', pathMatch: 'full' },
        { path: 'console', component: ConsoleComponent },
        { path: 'tests', component: TestListComponent },
        { path: 'history', component: JobHistoryComponent },
        { path: 'stats', component: JobStatsComponent },
        { path: 'downloads', component: JobDownloadsComponent },
        { path: 'document/:document_name', component: DocumentComponent }
    ]
}, {
    path: "dashboard/project/:project_id/build/:build_id",
    component: BuildDetailComponent
}
];

export const routing: ModuleWithProviders = RouterModule.forRoot(appRoutes);
