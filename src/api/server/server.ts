import express = require("express");
import http = require("http");
import https = require("https");
import fs = require("fs");

import * as _ from "lodash";

import { config } from "./config/config";
import { logger } from "./utils/logger";
import { Subscription } from "rxjs/Subscription";
import { ConsoleListener } from "./listeners/ConsoleListener";
import { JobListener } from "./listeners/JobListener";
import { ProjectToken, socket_token_auth } from "./utils/auth";

export function createServer(print: boolean) {
    const app = express();
    let server = null;

    if (config.api.tls.enabled) {
        logger.info("HTTPS is enabled");
        const options = {
            key: fs.readFileSync(config.api.tls.key),
            cert: fs.readFileSync(config.api.tls.cert)
        }

        server = https.createServer(options, app);
    } else {
        logger.warn("HTTPS is not enabled");
        server = http.createServer(app);
    }


    server['listeners']['console'] = new ConsoleListener();
    server['listeners']['job'] = new JobListener();

    require("./config/express")(app, config);
    const io = require("socket.io").listen(server, { transports: ['polling'] });

    let openConnections = 0;

    io.on("connection", (socket) => {
        logger.info("New socket connection");
        const subs = new Array<Subscription>();
        let isAuthenticated = false;
        let project_token: ProjectToken ;
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

        // disconnect if there's no auth message within a second
        setTimeout(() => {
            if (!isAuthenticated)  {
                logger.warn("no authentication message, closing socket");
                socket.disconnect();
            }
        }, 5000);

        socket.on("auth:token", (token: string) => {
            logger.info("auth:token: received");

            if (isAuthenticated) {
                logger.debug("auth:toke: already authenticated, closing socket");
                socket.disconnect();
                return;
            }

            socket_token_auth(token)
            .then((u: ProjectToken) => {
                project_token = u;
                isAuthenticated = true;
            })
            .catch((err) => {
                logger.warn(err);
                socket.disconnect();
            });
        });

        const subscribed_builds = new Set<string>();
        socket.on("listen:build", (build_id: string) => {
            logger.debug("listen:build:", build_id);

            if (!isAuthenticated) {
                logger.debug("listen:build - not authenticated");
                socket.disconnect();
                return;
            }

            if (!build_id) {
                logger.debug("listen:build: no build id");
                return;
            }

            if (!_.isString(build_id)) {
                logger.debug("listen:build: not a string");
                return;
            }

            if (subscribed_builds.has(build_id)) {
                logger.debug("listen:build: already subscribed");
                return;
            }

            subs.push(server['listeners']['job'].getJobs(project_token.project_id).subscribe((j) => {
                if (j.data.build.id === build_id) {
                    logger.debug("notify:job:", j);
                    socket.emit("notify:job", j);
                }
            }));

            subscribed_builds.add(build_id);
        });

        const subscribed_console = new Set<string>();
        socket.on("listen:console", (job_id: string) => {
            logger.debug("listen:console:", job_id);
            if (!isAuthenticated) {
                logger.debug("listen:console: not authenticated");
                socket.disconnect();
                return;
            }

            if (!job_id) {
                logger.debug("listen:console: no id");
                return;
            }

            if (!_.isString(job_id)) {
                logger.debug("listen:console: not a string");
                return;
            }

            if (subscribed_console.has(job_id)) {
                logger.debug("listen:console: already subscribed");
                return;
            }

            subs.push(server['listeners']['console'].getOutput(job_id, project_token.project_id).subscribe((output) => {
                logger.debug("notify:console:",  job_id);
                socket.emit("notify:console", {
                    data: output,
                    job_id: job_id
                });
            }));

            subscribed_console.add(job_id);
        });
    });

    const port = config.api.port;
    const x = server.listen(port);

    if (print) {
        logger.info("API server listening on port", port);
    }

    return x;
}

export function stopServer(server) {
    server.close();
}
