import { initDatabase } from "../db";

initDatabase((err) => {
    if (err) {
        console.error(err);
        process.exit(1);
    } else {
        console.info("Database successfully initialized");
        process.exit(0);
    }
});
