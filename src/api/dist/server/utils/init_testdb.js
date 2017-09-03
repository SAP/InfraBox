"use strict";
const db_1 = require("../db");
db_1.initDatabase((err) => {
    if (err) {
        console.error(err);
        process.exit(1);
    }
    else {
        console.info("Database successfully initialized");
        process.exit(0);
    }
});
