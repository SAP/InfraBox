# Badges
With InfraBox you can easily create one or mutiple badges like   or   with your custom information. To create a badge simply create a json file like this:

```json
{
    "version": 1,
    "subject": "build",
    "status": "failed",
    "color": "red"
}
```

and save it to `/infrabox/upload/badge/badge.json`. You can also save multiple files with different names in this directory. For every file a separate badge will be created.
