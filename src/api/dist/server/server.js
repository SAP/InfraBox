"use strict";
const express = require("express");
const http = require("http");
const _ = require("lodash");
const config_1 = require("./config/config");
const logger_1 = require("./utils/logger");
const ConsoleListener_1 = require("./listeners/ConsoleListener");
const JobListener_1 = require("./listeners/JobListener");
const auth_1 = require("./utils/auth");
function createServer(print) {
    const app = express();
    const server = http.createServer(app);
    server['listeners']['console'] = new ConsoleListener_1.ConsoleListener();
    server['listeners']['job'] = new JobListener_1.JobListener();
    require("./config/express")(app, config_1.config);
    const io = require("socket.io").listen(server, { transports: ['polling'] });
    let openConnections = 0;
    io.on("connection", (socket) => {
        logger_1.logger.info("New socket connection");
        const subs = new Array();
        let isAuthenticated = false;
        let user = null;
        openConnections += 1;
        socket.on("disconnect", () => {
            logger_1.logger.warn("disconnect, closing socket");
            for (const sub of subs) {
                sub.unsubscribe();
            }
            openConnections -= 1;
        });
        socket.on("error", (err) => {
            logger_1.logger.warn("error, closing socket", err);
            socket.disconnect();
        });
        // disconnect if there's no auth message within a second
        setTimeout(() => {
            if (!isAuthenticated) {
                logger_1.logger.warn("no authentication message, closing socket");
                socket.disconnect();
            }
        }, 5000);
        socket.on("auth:token", (token) => {
            logger_1.logger.info("auth:token: received");
            if (isAuthenticated) {
                logger_1.logger.debug("auth:toke: already authenticated, closing socket");
                socket.disconnect();
                return;
            }
            auth_1.socket_token_auth(token)
                .then((u) => {
                user = u;
                isAuthenticated = true;
            })
                .catch((err) => {
                logger_1.logger.warn(err);
                socket.disconnect();
            });
        });
        const subscribed_builds = new Set();
        socket.on("listen:build", (build_id) => {
            logger_1.logger.debug("listen:build:", build_id);
            if (!isAuthenticated) {
                logger_1.logger.debug("listen:build - not authenticated");
                socket.disconnect();
                return;
            }
            if (!build_id) {
                logger_1.logger.debug("listen:build: no build id");
                return;
            }
            if (!_.isString(build_id)) {
                logger_1.logger.debug("listen:build: not a string");
                return;
            }
            if (subscribed_builds.has(build_id)) {
                logger_1.logger.debug("listen:build: already subscribed");
                return;
            }
            subs.push(server['listeners']['job'].getJobs(user.id).subscribe((j) => {
                if (j.data.build.id === build_id) {
                    logger_1.logger.debug("notify:job:", j);
                    socket.emit("notify:job", j);
                }
            }));
            subscribed_builds.add(build_id);
        });
        const subscribed_console = new Set();
        socket.on("listen:console", (job_id) => {
            logger_1.logger.debug("listen:console:", job_id);
            if (!isAuthenticated) {
                logger_1.logger.debug("listen:console: not authenticated");
                socket.disconnect();
                return;
            }
            if (!job_id) {
                logger_1.logger.debug("listen:console: no id");
                return;
            }
            if (!_.isString(job_id)) {
                logger_1.logger.debug("listen:console: not a string");
                return;
            }
            if (subscribed_console.has(job_id)) {
                logger_1.logger.debug("listen:console: already subscribed");
                return;
            }
            subs.push(server['listeners']['console'].getOutput(job_id, user.id).subscribe((output) => {
                logger_1.logger.debug("notify:console:", job_id);
                socket.emit("notify:console", {
                    data: output,
                    job_id: job_id
                });
            }));
            subscribed_console.add(job_id);
        });
    });
    const port = config_1.config.api.port;
    const x = server.listen(port);
    if (print) {
        logger_1.logger.info("API server listening on port", port);
    }
    return x;
}
exports.createServer = createServer;
function stopServer(server) {
    server.close();
}
exports.stopServer = stopServer;
