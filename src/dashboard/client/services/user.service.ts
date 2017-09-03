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

export class AuthToken {
    public id: string;
    public description: string;
    public token: string;
    public scope_push = false;
    public scope_pull = false;
}

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

    public addAuthToken(token: AuthToken): Observable<Notification> {
        const url = this.url + '/token';
        const body = JSON.stringify({
            description: token.description,
            token: token.token,
            scope_pull: token.scope_pull,
            scope_push: token.scope_push
        });
        return this.api.post(url, body);
    }

    public deleteAuthToken(token: AuthToken): Observable<Notification> {
        const url = this.url + '/token/' + token.id;
        return this.api.delete(url);
    }

    public getAuthTokens(): Observable<AuthToken> {
        const url = this.url + '/token';

        return this.api.get(url).mergeMap((env: AuthToken[]) => {
            return Observable.from(env);
        });
    }

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
