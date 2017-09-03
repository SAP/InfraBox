"use strict";
const child_process = require("child_process");
const eachOf = require("async/eachOf");
const _ = require("lodash");
const status_1 = require("./utils/status");
const config_1 = require("./config/config");
const pgPromise = require("pg-promise");
const options = {};
exports.pgp = pgPromise(options);
exports.db = exports.pgp({
    host: config_1.config.database.host,
    port: config_1.config.database.port,
    database: config_1.config.database.db,
    user: config_1.config.database.user,
    password: config_1.config.database.password
});
function handleDBError(next) {
    return (err) => {
        if (err.infrabox_error) {
            // is our own error
            next(err);
        }
        else {
            return next(new status_1.InternalError(err));
        }
    };
}
exports.handleDBError = handleDBError;
function recreateDatabaseImpl() {
    const env = process.env.NODE_ENV || "development";
    if (env !== 'test') {
        /* tslint:disable */
        console.log("TRYING TO DROP NON-TEST DB");
        console.log("ABORTING");
        process.exit(1);
        return;
    }
    /* tslint:disable */
    let x = child_process.spawnSync("dropdb", ["--if-exists", "--user", "postgres", "test_db"]);
    if (x.status !== 0) {
        //console.log(x.stderr.toString("utf-8"));
        throw new Error("Database setup failed: could not drop");
    }
    x = child_process.spawnSync("psql", ["--user", "postgres", "-f", "./src/postgres/DB_ONLY_FOR_TESTING.sql"]);
    if (x.status != 0) {
        //console.log(x.stderr.toString("utf-8"));
        //console.log(x.stdout.toString("utf-8"));
        throw new Error("Database setup failed: could not create");
    }
    /* tslint:enable */
}
exports.recreateDatabase = _.once(recreateDatabaseImpl);
function initDatabase(cb) {
    const env = process.env.NODE_ENV || "development";
    if (env !== 'test') {
        /* tslint:disable */
        console.log("TRYING TO DROP NON-TEST DB");
        console.log("ABORTING");
        process.exit(1);
        return;
    }
    if (env === 'development') {
        exports.recreateDatabase();
    }
    exports.db.func("truncate_tables", ["postgres"])
        .then(() => {
        cb(null);
    }).catch(cb);
}
exports.initDatabase = initDatabase;
function insertData(data) {
    /* tslint:disable */
    return (cb) => {
        initDatabase((err) => {
            if (err) {
                return cb(err);
            }
            eachOf(data, (rows, table, cb2) => {
                let cols = _.keys(rows[0]);
                let stmt = exports.pgp.helpers.insert(rows, cols, table);
                exports.db.any(stmt).then(() => cb2()).catch((error) => {
                    console.log('Error for stmt:');
                    console.log(stmt);
                    console.log(error);
                    cb2(error);
                });
            }, cb);
        });
    };
    /* tslint:enable */
}
exports.insertData = insertData;
