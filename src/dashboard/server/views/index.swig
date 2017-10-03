<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>InfraBox | Login</title>

    <script src="/vendor.js"></script>
    <script src="/index.js"></script>
</head>

<body class="gray-bg">
    <div class="middle-box text-center loginscreen animated fadeInDown">
        <div>
            <div>
                <img src="/dist/images/logo_image_only.png" width="75%" />
            </div>
            <h3>Welcome to InfraBox</h3>
            {% if show_login_form %}
            <form class="m-t" role="form" action="/account/login" method="POST">
                <div class="form-group">
                    <input type="email" name="email" class="form-control" placeholder="Email" required="">
                </div>
                <div class="form-group">
                    <input type="password" name="password" class="form-control" placeholder="Password" required="">
                </div>
                {{ message }}
                <button type="submit" class="btn btn-info block full-width m-b"><i class="fa fa-sign-in"></i> Login</button>

                <a href="/account/register"><small><i class="fa fa-user-plus"></i> Create an account</small></a>
            </form>
            {% endif %}
            {% if github_login_enabled %}
            <br>
            <br>
            <a href="/github/auth" class="btn btn-info block full-width m-b"><i class="fa fa-github"></i> Login with GitHub</a>
            {% endif %}
        </div>
    </div>
</body>

</html>
