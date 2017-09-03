import express = require("express");
import http = require("http");

import * as _ from "lodash";

import { config } from "./config/config";
import { logger } from "./utils/logger";
import { Subscription } from "rxjs/Subscription";
import { ConsoleListener } from "./listeners/ConsoleListener";
import { JobListener } from "./listeners/JobListener";
import { socket_auth } from "./utils/auth";

export function createServer(print: boolean) {
    const app = express();
    const server = http.createServer(app);

    server['listeners']['console'] = new ConsoleListener();
    server['listeners']['job'] = new JobListener();

    require("./config/express")(app, config);
    const io = require("socket.io").listen(server, { transports: ['polling'] });

    let openConnections = 0;

    io.on("connection", (socket) => {
        logger.info("New socket connection");
        const subs = new Array<Subscription>();
        let user = null;
        openConnections += 1;

        socket.on("disconnect", () => {
            logger.warn("disconnect, closing socket");
            for (const sub of subs) {
                sub.unsubscribe();
            }

            openConnections -= 1;
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
