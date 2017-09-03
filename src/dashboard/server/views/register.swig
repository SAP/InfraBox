<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>InfraBox | Register</title>

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
            <form class="m-t" role="form" action="/account/register" method="POST">
                <div class="form-group">
                    <input type="username" name="username" class="form-control" placeholder="Username" required="">
                </div>
                <div class="form-group">
                    <input type="email" name="email" class="form-control" placeholder="Email" required="">
                </div>
                <div class="form-group">
                    <input type="password" name="password1" class="form-control" placeholder="Password" required="">
                </div>
                <div class="form-group">
                    <input type="password" name="password2" class="form-control" placeholder="Password" required="">
                </div>
                {{ message }}
                <button type="submit" class="btn btn-info block full-width m-b"><i class="fa fa-user-plus"></i> Sign up for InfraBox</button>
            </form>
        </div>
    </div>
</body>

</html>
