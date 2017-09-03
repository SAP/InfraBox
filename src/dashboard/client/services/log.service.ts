import { Injectable } from "@angular/core";

export interface Logger {
    info(...msg: any[]);
    warn(...msg: any[]);
    debug(...msg: any[]);
    error(...msg: any[]);
}

enum LogLevel {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4,
}

function toString(l: LogLevel) {
    switch (l) {
        case LogLevel.DEBUG: return "debug";
        case LogLevel.INFO: return "info ";
        case LogLevel.WARN: return "warn ";
        case LogLevel.ERROR: return "error";
        default:
            return "unknown";
    }
}

export class NamedLogger implements Logger {
    private name: string;
    private loglevel = LogLevel.DEBUG;

    constructor(name: string) {
        this.name = name;
    }

    public info(...msg: any[]) {
        msg.unshift(LogLevel.INFO);
        this.log.apply(this, msg);
    }

    public warn(...msg: any[]) {
        msg.unshift(LogLevel.WARN);
        this.log.apply(this, msg);
    }

    public debug(...msg: any[]) {
        msg.unshift(LogLevel.DEBUG);
        this.log.apply(this, msg);
    }

    public error(...msg: any[]) {
        msg.unshift(LogLevel.ERROR);
        this.log.apply(this, msg);
    }

    private log(level: LogLevel, ...msg: any[]) {
        if (level < this.loglevel) {
            return;
        }

        let d = new Date();
        let time = "";

        if (d.getHours() < 10) {
            time += "0";
        }
        time += d.getHours() + ":";

        if (d.getMinutes() < 10) {
            time += "0";
        }
        time += d.getMinutes() + ":";

        if (d.getSeconds() < 10) {
            time += "0";
        }
        time += d.getSeconds();

        let a = ["[", time, "][", toString(level), "][", this.name, "]"];

        for (let m of msg) {
            a.push(m);
        }

        console.log.apply(console.log, a);
    }
}

@Injectable()
export class LogService {
    public createNamedLogger(name: string) {
        return new NamedLogger(name);
    }
}
