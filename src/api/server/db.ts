import child_process = require("child_process");
const eachOf = require("async/eachOf");
import * as _ from "lodash";
import { logger } from "./utils/logger";
import { InternalError } from "./utils/status";
import { config } from "./config/config";

import * as pgPromise from "pg-promise";

const options = {};

export let pgp = pgPromise(options);
export let db = pgp({
    host: config.database.host,
    port: config.database.port,
    database: config.database.db,
    user: config.database.user,
    password: config.database.password
});

export function handleDBError(next) {
    return (err) => {
        if (err.infrabox_error) {
            // is our own error
            return next(err);
        } else if (err.error && err.error.message) {
            return next(new BadRequest(err.error.message));
        } else {
            return next(new InternalError(err));
        }
    };
}

function recreateDatabaseImpl() {
    const env = process.env.NODE_ENV || "development";
    if (env !== 'test') {
        /* tslint:disable */
        console.log("TRYING TO DROP NON-TEST DB");
        console.log("ABORTING");
        process.exit(1);
        return;
        /* tslint:enable */
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

export let recreateDatabase = _.once(recreateDatabaseImpl);

export function initDatabase(cb) {
    const env = process.env.NODE_ENV || "development";
    if (env !== 'test') {
        /* tslint:disable */
        console.log("TRYING TO DROP NON-TEST DB");
        console.log("ABORTING");
        process.exit(1);
        return;
        /* tslint:enable */
    }

    if (env === 'development') {
        recreateDatabase();
    }

    db.func("truncate_tables", ["postgres"])
        .then(() => {
            cb(null);
        }).catch(cb);
}

export function insertData(data) {
    /* tslint:disable */
    return (cb) => {
        initDatabase((err) => {
            if (err) {
                return cb(err);
            }

            eachOf(data, (rows, table, cb2) => {
                let cols = _.keys(rows[0]);
                let stmt = pgp.helpers.insert(rows, cols, table);
                db.any(stmt).then(() => cb2()).catch((error) => {
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
