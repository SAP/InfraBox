<html>

<head>
    <base href="/"/>
    <title>InfraBox</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="/favicon.ico" />
</head>

<body>
    <div id="wrapper">
        <benchbox-app></benchbox-app>
    </div>

    <script>
        var INFRABOX_DOCS_URL = "{{ INFRABOX_DOCS_URL }}";
        var INFRABOX_API_URL = "{{ INFRABOX_API_URL }}";
        var INFRABOX_GITHUB_ENABLED = {{ INFRABOX_GITHUB_ENABLED }};
    </script>

    <script src="vendor.js"></script>
    <script src="app.js"></script>

    <div class="modal inmodal" id="reconnectModal" tabindex="-1" role="dialog" aria-hidden="true" data-keyboard="false" data-backdrop="static">
        <div class="modal-dialog">
        <div class="modal-content">
                <div class="modal-header">
                    <i class="fa fa-laptop modal-icon"></i>
                    <h4 class="modal-title">Connection Lost</h4>
                    <small class="font-bold">You have been disconnected from InfraBox</small>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-info" onclick="location.reload()">Reload</button>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
