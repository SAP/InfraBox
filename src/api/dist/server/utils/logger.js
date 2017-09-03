"use strict";
const config_1 = require("../config/config");
var LogLevel;
(function (LogLevel) {
    LogLevel[LogLevel["DEBUG"] = 1] = "DEBUG";
    LogLevel[LogLevel["INFO"] = 2] = "INFO";
    LogLevel[LogLevel["WARN"] = 3] = "WARN";
    LogLevel[LogLevel["ERROR"] = 4] = "ERROR";
})(LogLevel || (LogLevel = {}));
function toString(l) {
    switch (l) {
        case LogLevel.DEBUG: return "debug";
        case LogLevel.INFO: return "info";
        case LogLevel.WARN: return "warn";
        case LogLevel.ERROR: return "error";
        default:
            return "unknown";
    }
}
function toLogLevel(l) {
    switch (l.toLowerCase()) {
        case "debug": return LogLevel.DEBUG;
        case "info": return LogLevel.INFO;
        case "warn": return LogLevel.WARN;
        case "error": return LogLevel.ERROR;
        default:
            return LogLevel.WARN;
    }
}
class Logger {
    constructor() {
        this.loglevel = toLogLevel(config_1.config.api.log.level);
    }
    info(...msg) {
        msg.unshift(LogLevel.INFO);
        this.log.apply(this, msg);
    }
    warn(...msg) {
        msg.unshift(LogLevel.WARN);
        this.log.apply(this, msg);
    }
    debug(...msg) {
        msg.unshift(LogLevel.DEBUG);
        this.log.apply(this, msg);
    }
    error(...msg) {
        msg.unshift(LogLevel.ERROR);
        this.log.apply(this, msg);
    }
    log(level, ...msg) {
        if (level < this.loglevel) {
            return;
        }
        if (config_1.config.api.log.stackdriver) {
            const eventTime = (new Date()).toISOString();
            const message = {
                eventTime,
                message: "",
                severity: toString(level).toUpperCase(),
                serviceContext: {
                    service: config_1.config.service.name,
                    version: config_1.config.service.version
                }
            };
            for (let m of msg) {
                if (m.stack) {
                    const stackTrace = Array.isArray(m.stack) ? m.stack.join("\n") : m.stack;
                    message.message += stackTrace + "\n";
                }
                else {
                    if (typeof m === 'object') {
                        m = JSON.stringify(m);
                    }
                    message.message += m + " ";
                }
            }
            msg = [JSON.stringify(message)];
        }
        switch (level) {
            case LogLevel.INFO:
                console.info.apply(console.info, msg);
                break;
            case LogLevel.WARN:
                console.warn.apply(console.warn, msg);
                break;
            case LogLevel.ERROR:
                console.error.apply(console.error, msg);
                break;
            default:
                return console.log.apply(console.log, msg);
        }
    }
}
exports.logger = new Logger();
exports.stream = {
    write: (message, encoding) => {
        if (message.length > 2 && message.charAt(message.length - 1) === "\n") {
            message = message.substr(0, message.length - 1);
        }
        exports.logger.info(message);
    }
};
