import { Injectable } from "@angular/core";

import { Observable } from "rxjs/Observable";
import { Logger, LogService } from "./log.service";
import { getToken } from "./login.service";

import io = require("socket.io-client");

@Injectable()
export class EventService {
    private host: string;
    private logger: Logger;
    private socket: SocketIOClient.Socket;

    constructor(private logService: LogService) {
        let protocol = 'ws:';

        if (window.location.protocol === 'https:') {
            protocol = 'wss:';
        }

        this.host = protocol + "//" + window.location.hostname + ":" + window.location.port;
        this.logger = logService.createNamedLogger("EventService");
        this.socket = io.connect(this.host, { transports: ['polling'] });

        this.socket.on("connect", () => {
            this.logger.info("connected");
        });

        this.socket.on("connect_error", (err) => {
            this.logger.info("connected_error", err);
        });

        this.socket.on("connect_timeout", () => {
            this.logger.info("connect_timeout");
        });

        this.socket.on("reconnect", (attempt) => {
            this.logger.info("reconnect", attempt);
        });

        this.socket.on("reconnect_attempt", (attempt) => {
            this.logger.info("reconnect", attempt);
        });

        this.socket.on("reconnecting", (attempt) => {
            this.logger.info("reconnect", attempt);
        });

        this.socket.on("reconnect_error", (error) => {
            this.logger.info("reconnect", error);
        });

        this.socket.on("reconnect_failed", () => {
            this.logger.info("reconnect");
        });

        this.socket.on("disconnect", () => {
            this.logger.warn("disconnected");
            this.socket.disconnect();
            this.socket.close();
            $('#reconnectModal')['modal']();
        });

        this.socket.on("error", (error: string) => {
            this.logger.error(`ERROR: "${error}" (${this.host})`);
            $('#reconnectModal')['modal']();
        });

        this.socket.emit('auth', getToken());
    }

    public listen(event: string, data = null): Observable<any> {
        const o = Observable.create((observer: any) => {
            const f = (item: any) => observer.next(item);
            this.socket.on("notify:" + event, f);
            return () => this.socket.removeListener("notify:" + event, f);
        });

        this.socket.emit("listen:" + event, data);
        return o;
    }
}
