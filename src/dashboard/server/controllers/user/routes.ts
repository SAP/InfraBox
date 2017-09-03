import { Router } from "express";
import { auth } from "../../utils/auth";

const p = Router();
p.use(auth);
p.use(require('./user.controller'));

module.exports = p;
