import { Injectable } from "@angular/core";
import { Response } from "@angular/http";
import { Observable } from "rxjs/Observable";
import { JwtHelper } from "angular2-jwt";
import { APIService } from "./api.service";
import { Notification } from "./notification.service";
import { LoginService } from "./login.service";

import "rxjs/add/operator/map";
import "rxjs/add/operator/catch";
import "rxjs/add/operator/do";
import 'rxjs/add/observable/from';

export class User {
    public id: string;
    public email: string;
    public username: string;
    public name: string;
    public avatar_url: string;
    public github_id: number;
}

@Injectable()
export class UserService {
    private url = "api/dashboard/user";
    constructor(private api: APIService, private loginService: LoginService) {}

    public isLoggedIn(): boolean {
        return this.loginService.isLoggedIn();
    }

    public logout() {
        this.loginService.logout();
    }

    public getUser(): Observable<User> {
        return this.api.get(this.url);
    }

    public hasGithubAccount(): Observable<boolean> {
        return this.getUser().map((u: User) => {
            return u.github_id !== null;
        });
    }

}
