import { Response } from "express";

export function NotFound() {
    this.name = "NotFound";
    this.message = "Not Found";
    this.status = 404;
    this.infrabox_error = true;
    this.ignore_error = true;
}
NotFound.prototype = Error.prototype;

export function BadRequest(message) {
    this.name = "BadRequest";
    this.message = (message || "Bad Request");
    this.status = 400;
    this.infrabox_error = true;
    this.ignore_error = true;
}
BadRequest.prototype = Error.prototype;

export function Unauthorized() {
    this.name = "Unauthorized";
    this.message = "Unauthorized";
    this.status = 401;
    this.infrabox_error = true;
    this.ignore_error = true;
}
Unauthorized.prototype = Error.prototype;

export function OK(res, message: string, data: any = null) {
    res.status(200);
    const m = { message: message, type: "success" };

    if (data) {
        m['data'] = data;
    }

    res.json(m);
}

export function InternalError(err: Error) {
    this.name = "InternalError";
    this.message = "Internal Server Error";
    this.details = err;
    this.status = 500;
    this.infrabox_error = true;
    this.ignore_error = false;
}
InternalError.prototype = Error.prototype;

export function CreateFinalHandler(res: Response, next, message: string) {
    return (err) => {
        if (err) {
            if (err.infrabox_error) {
                // just forward it
                return next(err);
            } else {
                // some other error, wrap it in out error
                return next(new InternalError(err));
            }
        }

        return OK(res, message);
    };
}
