import { Router } from "express";
import { auth } from "../../utils/auth";

const p = Router();
p.use(require('./auth.controller'));

module.exports = p;
