import { Injectable } from "@angular/core";
import { Response } from "@angular/http";
import { Observable } from "rxjs/Observable";
import { JwtHelper } from "angular2-jwt";
import { CanActivate } from '@angular/router';
import {CookieService} from 'angular2-cookie/core';

function getCookie(cname) {
    const name = cname + "=";
    const ca = document.cookie.split(';');
    for (let c of ca) {
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

export function getToken() {
    return getCookie("token");
}

@Injectable()
export class LoginService {
    private loggedIn = false;

    constructor(private cookieService: CookieService) {
        let token = this.cookieService.get("token");

        if (token) {
            const helper = new JwtHelper();
            const expired = helper.isTokenExpired(token);

            if (expired) {
                this.cookieService.remove("token");
                token = null;
            }
        }

        this.loggedIn = token != null;
    }

    public isLoggedIn(): boolean {
        return this.loggedIn;
    }

    public logout() {
        this.cookieService.remove("token");
        window.location.href = "/";
    }
}

@Injectable()
export class IsLoggedIn implements CanActivate {
    constructor(private loginService: LoginService) { }

    public canActivate() {
        return this.loginService.isLoggedIn();
    }
}
