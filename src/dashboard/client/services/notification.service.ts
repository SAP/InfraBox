import { Injectable } from "@angular/core";
import { Observable } from "rxjs/Observable";
import { Subject } from "rxjs/Subject";

export type NotificationType = "info" | "warning" | "error" | "success";

export class Notification {
    public data: any = null;
    constructor(public type: NotificationType, public message: string) { }
}

@Injectable()
export class NotificationService {
    private sub = new Subject<Notification>();

    public getNotifications(): Observable<Notification> {
        return this.sub;
    }

    public info(msg: string) {
        this.sub.next(new Notification("info", msg));
    }

    public warning(msg: string) {
        this.sub.next(new Notification("warning", msg));
    }

    public error(msg: string) {
        this.sub.next(new Notification("error", msg));
    }

    public success(msg: string) {
        this.sub.next(new Notification("success", msg));
    }

    public notify(n: Notification) {
        this.sub.next(n);
    }
}
