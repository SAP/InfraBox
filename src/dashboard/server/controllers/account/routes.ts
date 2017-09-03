import { Router } from "express";
import { config } from "../../config/config";

const p = Router();
if (config.account.signup.enabled) {
    p.use(require('./account.controller'));
} else if (config.account.ldap.enabled) {
    p.use(require('./ldap.controller'));
}

module.exports = p;
