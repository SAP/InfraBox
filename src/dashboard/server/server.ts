import express = require("express");
import http = require("http");
import https = require("https");
import fs = require("fs");
import prom = require('prom-client');

import * as _ from "lodash";

import { config } from "./config/config";
import { logger } from "./utils/logger";
import { Subscription } from "rxjs/Subscription";
import { ConsoleListener } from "./listeners/ConsoleListener";
import { JobListener } from "./listeners/JobListener";
import { socket_auth } from "./utils/auth";

const WEBSOCKET_CONNECTIONS = new prom.Gauge({
    name: "infrabox_dashboard_websocket_connections",
    help: "Number of open websocket connections"
});

const WEBSOCKET_EMIT_CONSOLE_UPDATE = new prom.Counter({
    name: "infrabox_dashboard_websocket_emit_console_update",
    help: "Number of emitted console updates"
});

const WEBSOCKET_EMIT_JOB_UPDATE = new prom.Counter({
    name: "infrabox_dashboard_websocket_emit_job_update",
    help: "Number of emitted job updates"
});

function createServerImpl(app): any {
    if (config.dashboard.tls.enabled) {
        logger.info("HTTPS is enabled");
        const options = {
            key: fs.readFileSync(config.dashboard.tls.key),
            cert: fs.readFileSync(config.dashboard.tls.cert)
        };

        return https.createServer(options, app);
    } else {
        logger.warn("HTTPS is not enabled");
        return http.createServer(app);
    }
}

function createMonitoringServerImpl() {
    const server = express();
    prom.collectDefaultMetrics();
    server.get('/metrics', (req, res) => {
        res.end(prom.register.metrics());
    });
    server.listen(config.dashboard.monitoring.port);
}

export function createServer(print: boolean) {
    const app = express();
    const server = createServerImpl(app);
    // createMonitoringServerImpl();

    server['listeners']['console'] = new ConsoleListener();
    server['listeners']['job'] = new JobListener();

    require("./config/express")(app, config);
    const io = require("socket.io").listen(server, {
        path: "/live/dashboard"
    });

    io.on("connection", (socket) => {
        logger.info("New socket connection");
        const subs = new Array<Subscription>();
        let user = null;

        WEBSOCKET_CONNECTIONS.inc();

        socket.on("disconnect", () => {
            logger.warn("disconnect, closing socket");
            for (const sub of subs) {
                sub.unsubscribe();
            }

            WEBSOCKET_CONNECTIONS.dec();
        });

        socket.on("error", (err) => {
            logger.warn("error, closing socket", err);
            socket.disconnect();
        });

        socket.on("auth", (token: string) => {
            logger.info("auth: received auth");

            if (!token) {
                return;
            }

            if (user) {
                logger.warn("auth: already authenticated, closing socket");
                socket.disconnect();
                return;
            }

            const u = socket_auth(token);

            if (!u) {
                logger.warn("auth: auth failed, closing socket");
                socket.disconnect();
                return;
            }

            user = u;
        });

        const subscribed_console = new Set<string>();
        socket.on("listen:console", (job_id: string) => {
            logger.debug("listen:console:", job_id);
            let user_id = null;

            if (!job_id) {
                logger.debug("listen:console: no id");
                return;
            }

            // TODO(Steffen): check is uuid
            if (!_.isString(job_id)) {
                logger.debug("listen:console: not a string");
                return;
            }

            if (subscribed_console.has(job_id)) {
                logger.debug("listen:console: already subscribed");
                return;
            }

            // TODO(Steffen): check is uuid
            if (user) {
                user_id = user.id;
            }

            subs.push(server['listeners']['console'].getOutput(job_id, user_id).subscribe((output) => {
                logger.debug("notify:console:",  job_id);
                WEBSOCKET_EMIT_CONSOLE_UPDATE.inc();
                socket.emit("notify:console", {
                    data: output,
                    job_id: job_id
                });
            }));

            subscribed_console.add(job_id);
        });

        const subscribed_projects = new Set<string>();
        socket.on("listen:jobs", (project_id: string) => {
            logger.info("listen:job:", project_id);
            let user_id = null;

            if (!project_id) {
                return;
            }

            if (!_.isString(project_id)) {
                return;
            }

            if (subscribed_projects.has(project_id)) {
                logger.debug("listen:jobs: already subscribed");
                return;
            }

            // TODO(Steffen): check is uuid
            if (user) {
                user_id = user.id;
            }

            subscribed_projects.add(project_id);

            subs.push(server['listeners']['job'].getJobs(user_id, project_id).subscribe((j) => {
                logger.debug("notify:jobs:", j);
                WEBSOCKET_EMIT_JOB_UPDATE.inc();
                socket.emit("notify:jobs", j);
            }));
        });
    });

    const port = config.dashboard.port;
    const x = server.listen(port);

    if (print) {
        logger.info("Express server listening on port", port);
    }

    return x;
}

export function stopServer(server) {
    server['listeners']['console'].stop();
    server['listeners']['job'].stop();
    server.close();
}
