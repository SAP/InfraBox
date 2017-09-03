import { config } from "../config/config";

enum LogLevel {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4,
}

function toString(l: LogLevel) {
    switch (l) {
        case LogLevel.DEBUG: return "debug";
        case LogLevel.INFO:  return "info";
        case LogLevel.WARN:  return "warn";
        case LogLevel.ERROR: return "error";
        default:
            return "unknown";
    }
}

function toLogLevel(l: string) {
    switch (l.toLowerCase()) {
        case "debug": return LogLevel.DEBUG;
        case "info":  return LogLevel.INFO;
        case "warn":  return LogLevel.WARN;
        case "error": return LogLevel.ERROR;
        default:
            return LogLevel.WARN;
    }
}

class Logger {
    private loglevel = toLogLevel(config.dashboard.log.level);

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

        if (config.dashboard.log.stackdriver) {
            const eventTime = (new Date()).toISOString();
            const message = {
                eventTime,
                message: "",
                severity: toString(level).toUpperCase(),
                serviceContext: {
                    service: config.service.name,
                    version: config.service.version
                }
            };

            for (let m of msg) {
                if (m.stack) {
                    const stackTrace = Array.isArray(m.stack) ? m.stack.join("\n") : m.stack;
                    message.message += stackTrace + "\n";
                } else {
                    if (typeof m === 'object') {
                        m = JSON.stringify(m);
                    }

                    message.message += m + " ";
                }
            }

            msg = [JSON.stringify(message)];
        }

        switch (level) {
            case LogLevel.INFO:  console.info.apply(console.info, msg); break;
            case LogLevel.WARN:  console.warn.apply(console.warn, msg); break;
            case LogLevel.ERROR: console.error.apply(console.error, msg); break;
            default:
                return console.log.apply(console.log, msg);
        }
    }
}

export const logger = new Logger();

export let stream = {
    write: (message: string, encoding) => {
        if (message.length > 2 && message.charAt(message.length - 1) === "\n") {
            message = message.substr(0, message.length - 1);
        }
        logger.info(message);
    }
};
