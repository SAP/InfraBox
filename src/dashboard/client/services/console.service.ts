import { Injectable } from "@angular/core";
import { ReplaySubject } from "rxjs/ReplaySubject";
import { Subscription } from "rxjs/Subscription";

import { EventService } from "../services/event.service";
import { Logger, LogService } from "../services/log.service";

export class ConsoleOutput {
    private subject = new ReplaySubject<string[]>();

    public subscribe(cb: (e: string[]) => void): Subscription {
        return this.subject.subscribe(cb);
    }

    public append(data: string) {
        if (!data) {
            return;
        }

        let lines = data.split("\n");
        this.subject.next(lines);
    }
}

class ConsoleEvent {
    public data: any;
    public job_id: string;
}

@Injectable()
export class ConsoleService {
    private consoles: Map<string, ConsoleOutput> = new Map<string, ConsoleOutput>();
    private logger: Logger;

    constructor(private eventService: EventService, private logService: LogService) {
        this.logger = logService.createNamedLogger("ConsoleService");
    }

    private listen(id: string) {
        if (this.consoles.has(id)) {
            return this.consoles.get(id);
        }

        let co = new ConsoleOutput();
        this.consoles.set(id, co);

        this.eventService.listen("console", id).filter((event: ConsoleEvent) => {
            return event.job_id === id;
        }).subscribe((event: ConsoleEvent) => {
            this.logger.debug("Received even: ", event);
            co.append(event.data as string);
        });
    }

    public getConsole(id: string): ConsoleOutput {
        this.listen(id);
        return this.consoles.get(id);
    }
}
