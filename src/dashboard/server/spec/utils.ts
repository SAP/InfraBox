import { config } from "../config/config";
const jwt = require("jsonwebtoken");

export function getToken(user_id: string): string {
    const token = jwt.sign({ user: { id: user_id, token: "" } }, config.dashboard.secret, { expiresIn: "7d" });
    return token;
}
