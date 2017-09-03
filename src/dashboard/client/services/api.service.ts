import { Logger, LogService } from "./log.service";
import { NotificationService, Notification } from "./notification.service";
import { LoginService } from "./login.service";

import { Http, Response, Headers, RequestOptions, ResponseContentType } from "@angular/http";
import { AuthHttp } from "angular2-jwt";
import { Injectable } from "@angular/core";
import { Observable } from "rxjs/Observable";
import { saveAs as importedSaveAs } from "file-saver";

import 'rxjs/add/observable/throw';

@Injectable()
export class APIService {
    private logger: Logger;
    private http: any;

    constructor(private logService: LogService,
        private authHttp: AuthHttp,
        private regularHttp: Http,
        private notification: NotificationService,
        private loginService: LoginService) {
        this.logger = logService.createNamedLogger("APIService");

        if (this.loginService.isLoggedIn()) {
            this.http = this.authHttp;
        } else {
            this.http = this.regularHttp;
        }
    }

    public get(url: string, data = {}): Observable<any> {
        const headers = new Headers({ 'Content-Type': 'application/json' });
        const options = new RequestOptions({ headers: headers, body: JSON.stringify(data) });

        return this.http
            .get(url, options)
            .map((res: Response) => res.json())
            .catch((error: Response | any) => {
                this.logger.error("error for: ", url);
                this.logger.error(error);

                if (error instanceof Response) {
                    this.logger.error("Response");
                    const body = error.json();
                    console.warn(body);
                    this.notification.notify(body as Notification);
                } else {
                    this.logger.error("no Response");
                    const errMsg = error.message ? error.message : error.toString();
                    console.error(errMsg);
                }
            });
    }

    public download(url: string, filename: string) {
        const headers = new Headers({ 'Content-Type': 'application/json' });
        const options = new RequestOptions({ headers: headers, responseType: ResponseContentType.Blob });
        return this.http
            .get(url, options)
            .map((res) => res.blob())
            .subscribe((blob) => {
                importedSaveAs(blob, filename);
            });
    }

    public delete(url: string): Observable<any> {
        return this.http
            .delete(url)
            .map((res: Response) => res.json())
            .catch((error: Response | any) => {
                this.logger.error("error for: ", url);
                this.logger.error(error);

                if (error instanceof Response) {
                    const body = error.json();
                    console.warn(body);
                    this.notification.notify(body as Notification);
                    return Observable.throw(body);
                } else {
                    const errMsg = error.message ? error.message : error.toString();
                    console.error(errMsg);
                    return Observable.throw(errMsg);
                }
            });
    }

    public post(url: string, body: string): Observable<Notification> {
        const headers = new Headers({ 'Content-Type': 'application/json' });
        const options = new RequestOptions({ headers: headers });
        return this.http
            .post(url, body, options)
            .map((res: Response) => res.json())
            .catch((error: Response | any) => {
                this.logger.error("error for: ", url);
                this.logger.error(error);

                if (error instanceof Response) {
                    const b = error.json();
                    console.warn(b);
                    this.notification.notify(b as Notification);
                    return Observable.throw(b);
                } else {
                    const errMsg = error.message ? error.message : error.toString();
                    console.error(errMsg);
                    return Observable.throw(errMsg);
                }
            });
    }
}
