# Cronjobs

It's possible to schedule jobs periodically. On the settings tab of your project you can add multiple cronjob entries.

- Name: can be any valid unique alphanumeric value
- Minute:       `0`-`59` and valid cron expression (`*`, `,`, `-`)
- Hour:         `0`-`23` and valid cron expression (`*`, `,`, `-`)
- Day of month: `1`-`31` and valid cron expression (`*`, `,`, `-`)
- Month:        `1`-`12` and valid cron expression (`*`, `,`, `-`)
- Day of week:  `0`-`6` and valid cron expression (`*`, `,`, `-`)
- Sha: git commit sha or branch name like `master`

InfraBox will schedule a new build for the specified time on the given branch or commit.
To build/test a certain project every night you may do it like this:

- Name: nightly
- Minute:       `0`
- Hour:         `3`
- Day of month: `*`
- Month:        `*`
- Day of week:  `1-6`
- Sha: `master`

This will schedule a build of the `master` branch every night at `3pm` from `monday` to `friday`.
