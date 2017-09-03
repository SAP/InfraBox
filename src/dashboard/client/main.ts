import { platformBrowserDynamic } from "@angular/platform-browser-dynamic";
import { enableProdMode } from "@angular/core";
import { AppModule } from "./app.module";

// TODO(Steffen): fix moment.js
enableProdMode();

const platform = platformBrowserDynamic();
platform.bootstrapModule(AppModule);

/* tslint:disable */
require('./css/style.css');
require('./css/benchbox.css');
require('./js/infrabox-page');
/* tslint:enable */
