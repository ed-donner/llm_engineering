# Authentication

- [Introduction](#introduction)
    - [Starter Kits](#starter-kits)
    - [Database Considerations](#introduction-database-considerations)
    - [Ecosystem Overview](#ecosystem-overview)
- [Authentication Quickstart](#authentication-quickstart)
    - [Install a Starter Kit](#install-a-starter-kit)
    - [Retrieving the Authenticated User](#retrieving-the-authenticated-user)
    - [Protecting Routes](#protecting-routes)
    - [Login Throttling](#login-throttling)
- [Manually Authenticating Users](#authenticating-users)
    - [Remembering Users](#remembering-users)
    - [Other Authentication Methods](#other-authentication-methods)
- [HTTP Basic Authentication](#http-basic-authentication)
    - [Stateless HTTP Basic Authentication](#stateless-http-basic-authentication)
- [Logging Out](#logging-out)
    - [Invalidating Sessions on Other Devices](#invalidating-sessions-on-other-devices)
- [Password Confirmation](#password-confirmation)
    - [Configuration](#password-confirmation-configuration)
    - [Routing](#password-confirmation-routing)
    - [Protecting Routes](#password-confirmation-protecting-routes)
- [Adding Custom Guards](#adding-custom-guards)
    - [Closure Request Guards](#closure-request-guards)
- [Adding Custom User Providers](#adding-custom-user-providers)
    - [The User Provider Contract](#the-user-provider-contract)
    - [The Authenticatable Contract](#the-authenticatable-contract)
- [Automatic Password Rehashing](#automatic-password-rehashing)
- [Social Authentication](/docs/{{version}}/socialite)
- [Events](#events)

<a name="introduction"></a>
## Introduction

Many web applications provide a way for their users to authenticate with the application and "login". Implementing this feature in web applications can be a complex and potentially risky endeavor. For this reason, Laravel strives to give you the tools you need to implement authentication quickly, securely, and easily.

At its core, Laravel's authentication facilities are made up of "guards" and "providers". Guards define how users are authenticated for each request. For example, Laravel ships with a `session` guard which maintains state using session storage and cookies.

Providers define how users are retrieved from your persistent storage. Laravel ships with support for retrieving users using [Eloquent](/docs/{{version}}/eloquent) and the database query builder. However, you are free to define additional providers as needed for your application.

Your application's authentication configuration file is located at `config/auth.php`. This file contains several well-documented options for tweaking the behavior of Laravel's authentication services.

> [!NOTE]  
> Guards and providers should not be confused with "roles" and "permissions". To learn more about authorizing user actions via permissions, please refer to the [authorization](/docs/{{version}}/authorization) documentation.

<a name="starter-kits"></a>
### Starter Kits

Want to get started fast? Install a [Laravel application starter kit](/docs/{{version}}/starter-kits) in a fresh Laravel application. After migrating your database, navigate your browser to `/register` or any other URL that is assigned to your application. The starter kits will take care of scaffolding your entire authentication system!

**Even if you choose not to use a starter kit in your final Laravel application, installing the [Laravel Breeze](/docs/{{version}}/starter-kits#laravel-breeze) starter kit can be a wonderful opportunity to learn how to implement all of Laravel's authentication functionality in an actual Laravel project.** Since Laravel Breeze creates authentication controllers, routes, and views for you, you can examine the code within these files to learn how Laravel's authentication features may be implemented.

<a name="introduction-database-considerations"></a>
### Database Considerations

By default, Laravel includes an `App\Models\User` [Eloquent model](/docs/{{version}}/eloquent) in your `app/Models` directory. This model may be used with the default Eloquent authentication driver.

If your application is not using Eloquent, you may use the `database` authentication provider which uses the Laravel query builder. If your application is using MongoDB, check out MongoDB's official [Laravel user authentication documentation](https://www.mongodb.com/docs/drivers/php/laravel-mongodb/current/user-authentication/) .

When building the database schema for the `App\Models\User` model, make sure the password column is at least 60 characters in length. Of course, the `users` table migration that is included in new Laravel applications already creates a column that exceeds this length.

Also, you should verify that your `users` (or equivalent) table contains a nullable, string `remember_token` column of 100 characters. This column will be used to store a token for users that select the "remember me" option when logging into your application. Again, the default `users` table migration that is included in new Laravel applications already contains this column.

<a name="ecosystem-overview"></a>
### Ecosystem Overview

Laravel offers several packages related to authentication. Before continuing, we'll review the general authentication ecosystem in Laravel and discuss each package's intended purpose.

First, consider how authentication works. When using a web browser, a user will provide their username and password via a login form. If these credentials are correct, the application will store information about the authenticated user in the user's [session](/docs/{{version}}/session). A cookie issued to the browser contains the session ID so that subsequent requests to the application can associate the user with the correct session. After the session cookie is received, the application will retrieve the session data based on the session ID, note that the authentication information has been stored in the session, and will consider the user as "authenticated".

When a remote service needs to authenticate to access an API, cookies are not typically used for authentication because there is no web browser. Instead, the remote service sends an API token to the API on each request. The application may validate the incoming token against a table of valid API tokens and "authenticate" the request as being performed by the user associated with that API token.

<a name="laravels-built-in-browser-authentication-services"></a>
#### Laravel's Built-in Browser Authentication Services

Laravel includes built-in authentication and session services which are typically accessed via the `Auth` and `Session` facades. These features provide cookie-based authentication for requests that are initiated from web browsers. They provide methods that allow you to verify a user's credentials and authenticate the user. In addition, these services will automatically store the proper authentication data in the user's session and issue the user's session cookie. A discussion of how to use these services is contained within this documentation.

**Application Starter Kits**

As discussed in this documentation, you can interact with these authentication services manually to build your application's own authentication layer. However, to help you get started more quickly, we have released [free packages](/docs/{{version}}/starter-kits) that provide robust, modern scaffolding of the entire authentication layer. These packages are [Laravel Breeze](/docs/{{version}}/starter-kits#laravel-breeze), [Laravel Jetstream](/docs/{{version}}/starter-kits#laravel-jetstream), and [Laravel Fortify](/docs/{{version}}/fortify).

_Laravel Breeze_ is a simple, minimal implementation of all of Laravel's authentication features, including login, registration, password reset, email verification, and password confirmation. Laravel Breeze's view layer is comprised of simple [Blade templates](/docs/{{version}}/blade) styled with [Tailwind CSS](https://tailwindcss.com). To get started, check out the documentation on Laravel's [application starter kits](/docs/{{version}}/starter-kits).

_Laravel Fortify_ is a headless authentication backend for Laravel that implements many of the features found in this documentation, including cookie-based authentication as well as other features such as two-factor authentication and email verification. Fortify provides the authentication backend for Laravel Jetstream or may be used independently in combination with [Laravel Sanctum](/docs/{{version}}/sanctum) to provide authentication for an SPA that needs to authenticate with Laravel.

_[Laravel Jetstream](https://jetstream.laravel.com)_ is a robust application starter kit that consumes and exposes Laravel Fortify's authentication services with a beautiful, modern UI powered by [Tailwind CSS](https://tailwindcss.com), [Livewire](https://livewire.laravel.com), and / or [Inertia](https://inertiajs.com). Laravel Jetstream includes optional support for two-factor authentication, team support, browser session management, profile management, and built-in integration with [Laravel Sanctum](/docs/{{version}}/sanctum) to offer API token authentication. Laravel's API authentication offerings are discussed below.

<a name="laravels-api-authentication-services"></a>
#### Laravel's API Authentication Services

Laravel provides two optional packages to assist you in managing API tokens and authenticating requests made with API tokens: [Passport](/docs/{{version}}/passport) and [Sanctum](/docs/{{version}}/sanctum). Please note that these libraries and Laravel's built-in cookie based authentication libraries are not mutually exclusive. These libraries primarily focus on API token authentication while the built-in authentication services focus on cookie based browser authentication. Many applications will use both Laravel's built-in cookie based authentication services and one of Laravel's API authentication packages.

**Passport**

Passport is an OAuth2 authentication provider, offering a variety of OAuth2 "grant types" which allow you to issue various types of tokens. In general, this is a robust and complex package for API authentication. However, most applications do not require the complex features offered by the OAuth2 spec, which can be confusing for both users and developers. In addition, developers have been historically confused about how to authenticate SPA applications or mobile applications using OAuth2 authentication providers like Passport.

**Sanctum**

In response to the complexity of OAuth2 and developer confusion, we set out to build a simpler, more streamlined authentication package that could handle both first-party web requests from a web browser and API requests via tokens. This goal was realized with the release of [Laravel Sanctum](/docs/{{version}}/sanctum), which should be considered the preferred and recommended authentication package for applications that will be offering a first-party web UI in addition to an API, or will be powered by a single-page application (SPA) that exists separately from the backend Laravel application, or applications that offer a mobile client.

Laravel Sanctum is a hybrid web / API authentication package that can manage your application's entire authentication process. This is possible because when Sanctum based applications receive a request, Sanctum will first determine if the request includes a session cookie that references an authenticated session. Sanctum accomplishes this by calling Laravel's built-in authentication services which we discussed earlier. If the request is not being authenticated via a session cookie, Sanctum will inspect the request for an API token. If an API token is present, Sanctum will authenticate the request using that token. To learn more about this process, please consult Sanctum's ["how it works"](/docs/{{version}}/sanctum#how-it-works) documentation.

Laravel Sanctum is the API package we have chosen to include with the [Laravel Jetstream](https://jetstream.laravel.com) application starter kit because we believe it is the best fit for the majority of web application's authentication needs.

<a name="summary-choosing-your-stack"></a>
#### Summary and Choosing Your Stack

In summary, if your application will be accessed using a browser and you are building a monolithic Laravel application, your application will use Laravel's built-in authentication services.

Next, if your application offers an API that will be consumed by third parties, you will choose between [Passport](/docs/{{version}}/passport) or [Sanctum](/docs/{{version}}/sanctum) to provide API token authentication for your application. In general, Sanctum should be preferred when possible since it is a simple, complete solution for API authentication, SPA authentication, and mobile authentication, including support for "scopes" or "abilities".

If you are building a single-page application (SPA) that will be powered by a Laravel backend, you should use [Laravel Sanctum](/docs/{{version}}/sanctum). When using Sanctum, you will either need to [manually implement your own backend authentication routes](#authenticating-users) or utilize [Laravel Fortify](/docs/{{version}}/fortify) as a headless authentication backend service that provides routes and controllers for features such as registration, password reset, email verification, and more.

Passport may be chosen when your application absolutely needs all of the features provided by the OAuth2 specification.

And, if you would like to get started quickly, we are pleased to recommend [Laravel Breeze](/docs/{{version}}/starter-kits#laravel-breeze) as a quick way to start a new Laravel application that already uses our preferred authentication stack of Laravel's built-in authentication services and Laravel Sanctum.

<a name="authentication-quickstart"></a>
## Authentication Quickstart

> [!WARNING]  
> This portion of the documentation discusses authenticating users via the [Laravel application starter kits](/docs/{{version}}/starter-kits), which includes UI scaffolding to help you get started quickly. If you would like to integrate with Laravel's authentication systems directly, check out the documentation on [manually authenticating users](#authenticating-users).

<a name="install-a-starter-kit"></a>
### Install a Starter Kit

First, you should [install a Laravel application starter kit](/docs/{{version}}/starter-kits). Our current starter kits, Laravel Breeze and Laravel Jetstream, offer beautifully designed starting points for incorporating authentication into your fresh Laravel application.

Laravel Breeze is a minimal, simple implementation of all of Laravel's authentication features, including login, registration, password reset, email verification, and password confirmation. Laravel Breeze's view layer is made up of simple [Blade templates](/docs/{{version}}/blade) styled with [Tailwind CSS](https://tailwindcss.com). Additionally, Breeze provides scaffolding options based on [Livewire](https://livewire.laravel.com) or [Inertia](https://inertiajs.com), with the choice of using Vue or React for the Inertia-based scaffolding.

[Laravel Jetstream](https://jetstream.laravel.com) is a more robust application starter kit that includes support for scaffolding your application with [Livewire](https://livewire.laravel.com) or [Inertia and Vue](https://inertiajs.com). In addition, Jetstream features optional support for two-factor authentication, teams, profile management, browser session management, API support via [Laravel Sanctum](/docs/{{version}}/sanctum), account deletion, and more.

<a name="retrieving-the-authenticated-user"></a>
### Retrieving the Authenticated User

After installing an authentication starter kit and allowing users to register and authenticate with your application, you will often need to interact with the currently authenticated user. While handling an incoming request, you may access the authenticated user via the `Auth` facade's `user` method:

    use Illuminate\Support\Facades\Auth;

    // Retrieve the currently authenticated user...
    $user = Auth::user();

    // Retrieve the currently authenticated user's ID...
    $id = Auth::id();

Alternatively, once a user is authenticated, you may access the authenticated user via an `Illuminate\Http\Request` instance. Remember, type-hinted classes will automatically be injected into your controller methods. By type-hinting the `Illuminate\Http\Request` object, you may gain convenient access to the authenticated user from any controller method in your application via the request's `user` method:

    <?php

    namespace App\Http\Controllers;

    use Illuminate\Http\RedirectResponse;
    use Illuminate\Http\Request;

    class FlightController extends Controller
    {
        /**
         * Update the flight information for an existing flight.
         */
        public function update(Request $request): RedirectResponse
        {
            $user = $request->user();

            // ...

            return redirect('/flights');
        }
    }

<a name="determining-if-the-current-user-is-authenticated"></a>
#### Determining if the Current User is Authenticated

To determine if the user making the incoming HTTP request is authenticated, you may use the `check` method on the `Auth` facade. This method will return `true` if the user is authenticated:

    use Illuminate\Support\Facades\Auth;

    if (Auth::check()) {
        // The user is logged in...
    }

> [!NOTE]  
> Even though it is possible to determine if a user is authenticated using the `check` method, you will typically use a middleware to verify that the user is authenticated before allowing the user access to certain routes / controllers. To learn more about this, check out the documentation on [protecting routes](/docs/{{version}}/authentication#protecting-routes).

<a name="protecting-routes"></a>
### Protecting Routes

[Route middleware](/docs/{{version}}/middleware) can be used to only allow authenticated users to access a given route. Laravel ships with an `auth` middleware, which is a [middleware alias](/docs/{{version}}/middleware#middleware-aliases) for the `Illuminate\Auth\Middleware\Authenticate` class. Since this middleware is already aliased internally by Laravel, all you need to do is attach the middleware to a route definition:

    Route::get('/flights', function () {
        // Only authenticated users may access this route...
    })->middleware('auth');

<a name="redirecting-unauthenticated-users"></a>
#### Redirecting Unauthenticated Users

When the `auth` middleware detects an unauthenticated user, it will redirect the user to the `login` [named route](/docs/{{version}}/routing#named-routes). You may modify this behavior using the method `redirectGuestsTo` of your application's `bootstrap/app.php` file:

    use Illuminate\Http\Request;

    ->withMiddleware(function (Middleware $middleware) {
        $middleware->redirectGuestsTo('/login');

        // Using a closure...
        $middleware->redirectGuestsTo(fn (Request $request) => route('login'));
    })

<a name="specifying-a-guard"></a>
#### Specifying a Guard

When attaching the `auth` middleware to a route, you may also specify which "guard" should be used to authenticate the user. The guard specified should correspond to one of the keys in the `guards` array of your `auth.php` configuration file:

    Route::get('/flights', function () {
        // Only authenticated users may access this route...
    })->middleware('auth:admin');

<a name="login-throttling"></a>
### Login Throttling

If you are using the Laravel Breeze or Laravel Jetstream [starter kits](/docs/{{version}}/starter-kits), rate limiting will automatically be applied to login attempts. By default, the user will not be able to login for one minute if they fail to provide the correct credentials after several attempts. The throttling is unique to the user's username / email address and their IP address.

> [!NOTE]  
> If you would like to rate limit other routes in your application, check out the [rate limiting documentation](/docs/{{version}}/routing#rate-limiting).

<a name="authenticating-users"></a>
## Manually Authenticating Users

You are not required to use the authentication scaffolding included with Laravel's [application starter kits](/docs/{{version}}/starter-kits). If you choose not to use this scaffolding, you will need to manage user authentication using the Laravel authentication classes directly. Don't worry, it's a cinch!

We will access Laravel's authentication services via the `Auth` [facade](/docs/{{version}}/facades), so we'll need to make sure to import the `Auth` facade at the top of the class. Next, let's check out the `attempt` method. The `attempt` method is normally used to handle authentication attempts from your application's "login" form. If authentication is successful, you should regenerate the user's [session](/docs/{{version}}/session) to prevent [session fixation](https://en.wikipedia.org/wiki/Session_fixation):

    <?php

    namespace App\Http\Controllers;

    use Illuminate\Http\Request;
    use Illuminate\Http\RedirectResponse;
    use Illuminate\Support\Facades\Auth;

    class LoginController extends Controller
    {
        /**
         * Handle an authentication attempt.
         */
        public function authenticate(Request $request): RedirectResponse
        {
            $credentials = $request->validate([
                'email' => ['required', 'email'],
                'password' => ['required'],
            ]);

            if (Auth::attempt($credentials)) {
                $request->session()->regenerate();

                return redirect()->intended('dashboard');
            }

            return back()->withErrors([
                'email' => 'The provided credentials do not match our records.',
            ])->onlyInput('email');
        }
    }

The `attempt` method accepts an array of key / value pairs as its first argument. The values in the array will be used to find the user in your database table. So, in the example above, the user will be retrieved by the value of the `email` column. If the user is found, the hashed password stored in the database will be compared with the `password` value passed to the method via the array. You should not hash the incoming request's `password` value, since the framework will automatically hash the value before comparing it to the hashed password in the database. An authenticated session will be started for the user if the two hashed passwords match.

Remember, Laravel's authentication services will retrieve users from your database based on your authentication guard's "provider" configuration. In the default `config/auth.php` configuration file, the Eloquent user provider is specified and it is instructed to use the `App\Models\User` model when retrieving users. You may change these values within your configuration file based on the needs of your application.

The `attempt` method will return `true` if authentication was successful. Otherwise, `false` will be returned.

The `intended` method provided by Laravel's redirector will redirect the user to the URL they were attempting to access before being intercepted by the authentication middleware. A fallback URI may be given to this method in case the intended destination is not available.

<a name="specifying-additional-conditions"></a>
#### Specifying Additional Conditions

If you wish, you may also add extra query conditions to the authentication query in addition to the user's email and password. To accomplish this, we may simply add the query conditions to the array passed to the `attempt` method. For example, we may verify that the user is marked as "active":

    if (Auth::attempt(['email' => $email, 'password' => $password, 'active' => 1])) {
        // Authentication was successful...
    }

For complex query conditions, you may provide a closure in your array of credentials. This closure will be invoked with the query instance, allowing you to customize the query based on your application's needs:

    use Illuminate\Database\Eloquent\Builder;

    if (Auth::attempt([
        'email' => $email,
        'password' => $password,
        fn (Builder $query) => $query->has('activeSubscription'),
    ])) {
        // Authentication was successful...
    }

> [!WARNING]  
> In these examples, `email` is not a required option, it is merely used as an example. You should use whatever column name corresponds to a "username" in your database table.

The `attemptWhen` method, which receives a closure as its second argument, may be used to perform more extensive inspection of the potential user before actually authenticating the user. The closure receives the potential user and should return `true` or `false` to indicate if the user may be authenticated:

    if (Auth::attemptWhen([
        'email' => $email,
        'password' => $password,
    ], function (User $user) {
        return $user->isNotBanned();
    })) {
        // Authentication was successful...
    }

<a name="accessing-specific-guard-instances"></a>
#### Accessing Specific Guard Instances

Via the `Auth` facade's `guard` method, you may specify which guard instance you would like to utilize when authenticating the user. This allows you to manage authentication for separate parts of your application using entirely separate authenticatable models or user tables.

The guard name passed to the `guard` method should correspond to one of the guards configured in your `auth.php` configuration file:

    if (Auth::guard('admin')->attempt($credentials)) {
        // ...
    }

<a name="remembering-users"></a>
### Remembering Users

Many web applications provide a "remember me" checkbox on their login form. If you would like to provide "remember me" functionality in your application, you may pass a boolean value as the second argument to the `attempt` method.

When this value is `true`, Laravel will keep the user authenticated indefinitely or until they manually logout. Your `users` table must include the string `remember_token` column, which will be used to store the "remember me" token. The `users` table migration included with new Laravel applications already includes this column:

    use Illuminate\Support\Facades\Auth;

    if (Auth::attempt(['email' => $email, 'password' => $password], $remember)) {
        // The user is being remembered...
    }

If your application offers "remember me" functionality, you may use the `viaRemember`  method to determine if the currently authenticated user was authenticated using the "remember me" cookie:

    use Illuminate\Support\Facades\Auth;

    if (Auth::viaRemember()) {
        // ...
    }

<a name="other-authentication-methods"></a>
### Other Authentication Methods

<a name="authenticate-a-user-instance"></a>
#### Authenticate a User Instance

If you need to set an existing user instance as the currently authenticated user, you may pass the user instance to the `Auth` facade's `login` method. The given user instance must be an implementation of the `Illuminate\Contracts\Auth\Authenticatable` [contract](/docs/{{version}}/contracts). The `App\Models\User` model included with Laravel already implements this interface. This method of authentication is useful when you already have a valid user instance, such as directly after a user registers with your application:

    use Illuminate\Support\Facades\Auth;

    Auth::login($user);

You may pass a boolean value as the second argument to the `login` method. This value indicates if "remember me" functionality is desired for the authenticated session. Remember, this means that the session will be authenticated indefinitely or until the user manually logs out of the application:

    Auth::login($user, $remember = true);

If needed, you may specify an authentication guard before calling the `login` method:

    Auth::guard('admin')->login($user);

<a name="authenticate-a-user-by-id"></a>
#### Authenticate a User by ID

To authenticate a user using their database record's primary key, you may use the `loginUsingId` method. This method accepts the primary key of the user you wish to authenticate:

    Auth::loginUsingId(1);

You may pass a boolean value to the `remember` argument of the `loginUsingId` method. This value indicates if "remember me" functionality is desired for the authenticated session. Remember, this means that the session will be authenticated indefinitely or until the user manually logs out of the application:

    Auth::loginUsingId(1, remember: true);

<a name="authenticate-a-user-once"></a>
#### Authenticate a User Once

You may use the `once` method to authenticate a user with the application for a single request. No sessions or cookies will be utilized when calling this method:

    if (Auth::once($credentials)) {
        // ...
    }

<a name="http-basic-authentication"></a>
## HTTP Basic Authentication

[HTTP Basic Authentication](https://en.wikipedia.org/wiki/Basic_access_authentication) provides a quick way to authenticate users of your application without setting up a dedicated "login" page. To get started, attach the `auth.basic` [middleware](/docs/{{version}}/middleware) to a route. The `auth.basic` middleware is included with the Laravel framework, so you do not need to define it:

    Route::get('/profile', function () {
        // Only authenticated users may access this route...
    })->middleware('auth.basic');

Once the middleware has been attached to the route, you will automatically be prompted for credentials when accessing the route in your browser. By default, the `auth.basic` middleware will assume the `email` column on your `users` database table is the user's "username".

<a name="a-note-on-fastcgi"></a>
#### A Note on FastCGI

If you are using PHP FastCGI and Apache to serve your Laravel application, HTTP Basic authentication may not work correctly. To correct these problems, the following lines may be added to your application's `.htaccess` file:

```apache
RewriteCond %{HTTP:Authorization} ^(.+)$
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
```

<a name="stateless-http-basic-authentication"></a>
### Stateless HTTP Basic Authentication

You may also use HTTP Basic Authentication without setting a user identifier cookie in the session. This is primarily helpful if you choose to use HTTP Authentication to authenticate requests to your application's API. To accomplish this, [define a middleware](/docs/{{version}}/middleware) that calls the `onceBasic` method. If no response is returned by the `onceBasic` method, the request may be passed further into the application:

    <?php

    namespace App\Http\Middleware;

    use Closure;
    use Illuminate\Http\Request;
    use Illuminate\Support\Facades\Auth;
    use Symfony\Component\HttpFoundation\Response;

    class AuthenticateOnceWithBasicAuth
    {
        /**
         * Handle an incoming request.
         *
         * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
         */
        public function handle(Request $request, Closure $next): Response
        {
            return Auth::onceBasic() ?: $next($request);
        }

    }

Next, attach the middleware to a route:

    Route::get('/api/user', function () {
        // Only authenticated users may access this route...
    })->middleware(AuthenticateOnceWithBasicAuth::class);

<a name="logging-out"></a>
## Logging Out

To manually log users out of your application, you may use the `logout` method provided by the `Auth` facade. This will remove the authentication information from the user's session so that subsequent requests are not authenticated.

In addition to calling the `logout` method, it is recommended that you invalidate the user's session and regenerate their [CSRF token](/docs/{{version}}/csrf). After logging the user out, you would typically redirect the user to the root of your application:

    use Illuminate\Http\Request;
    use Illuminate\Http\RedirectResponse;
    use Illuminate\Support\Facades\Auth;

    /**
     * Log the user out of the application.
     */
    public function logout(Request $request): RedirectResponse
    {
        Auth::logout();

        $request->session()->invalidate();

        $request->session()->regenerateToken();

        return redirect('/');
    }

<a name="invalidating-sessions-on-other-devices"></a>
### Invalidating Sessions on Other Devices

Laravel also provides a mechanism for invalidating and "logging out" a user's sessions that are active on other devices without invalidating the session on their current device. This feature is typically utilized when a user is changing or updating their password and you would like to invalidate sessions on other devices while keeping the current device authenticated.

Before getting started, you should make sure that the `Illuminate\Session\Middleware\AuthenticateSession` middleware is included on the routes that should receive session authentication. Typically, you should place this middleware on a route group definition so that it can be applied to the majority of your application's routes. By default, the `AuthenticateSession` middleware may be attached to a route using the `auth.session` [middleware alias](/docs/{{version}}/middleware#middleware-aliases):

    Route::middleware(['auth', 'auth.session'])->group(function () {
        Route::get('/', function () {
            // ...
        });
    });

Then, you may use the `logoutOtherDevices` method provided by the `Auth` facade. This method requires the user to confirm their current password, which your application should accept through an input form:

    use Illuminate\Support\Facades\Auth;

    Auth::logoutOtherDevices($currentPassword);

When the `logoutOtherDevices` method is invoked, the user's other sessions will be invalidated entirely, meaning they will be "logged out" of all guards they were previously authenticated by.

<a name="password-confirmation"></a>
## Password Confirmation

While building your application, you may occasionally have actions that should require the user to confirm their password before the action is performed or before the user is redirected to a sensitive area of the application. Laravel includes built-in middleware to make this process a breeze. Implementing this feature will require you to define two routes: one route to display a view asking the user to confirm their password and another route to confirm that the password is valid and redirect the user to their intended destination.

> [!NOTE]  
> The following documentation discusses how to integrate with Laravel's password confirmation features directly; however, if you would like to get started more quickly, the [Laravel application starter kits](/docs/{{version}}/starter-kits) include support for this feature!

<a name="password-confirmation-configuration"></a>
### Configuration

After confirming their password, a user will not be asked to confirm their password again for three hours. However, you may configure the length of time before the user is re-prompted for their password by changing the value of the `password_timeout` configuration value within your application's `config/auth.php` configuration file.

<a name="password-confirmation-routing"></a>
### Routing

<a name="the-password-confirmation-form"></a>
#### The Password Confirmation Form

First, we will define a route to display a view that requests the user to confirm their password:

    Route::get('/confirm-password', function () {
        return view('auth.confirm-password');
    })->middleware('auth')->name('password.confirm');

As you might expect, the view that is returned by this route should have a form containing a `password` field. In addition, feel free to include text within the view that explains that the user is entering a protected area of the application and must confirm their password.

<a name="confirming-the-password"></a>
#### Confirming the Password

Next, we will define a route that will handle the form request from the "confirm password" view. This route will be responsible for validating the password and redirecting the user to their intended destination:

    use Illuminate\Http\Request;
    use Illuminate\Support\Facades\Hash;
    use Illuminate\Support\Facades\Redirect;

    Route::post('/confirm-password', function (Request $request) {
        if (! Hash::check($request->password, $request->user()->password)) {
            return back()->withErrors([
                'password' => ['The provided password does not match our records.']
            ]);
        }

        $request->session()->passwordConfirmed();

        return redirect()->intended();
    })->middleware(['auth', 'throttle:6,1']);

Before moving on, let's examine this route in more detail. First, the request's `password` field is determined to actually match the authenticated user's password. If the password is valid, we need to inform Laravel's session that the user has confirmed their password. The `passwordConfirmed` method will set a timestamp in the user's session that Laravel can use to determine when the user last confirmed their password. Finally, we can redirect the user to their intended destination.

<a name="password-confirmation-protecting-routes"></a>
### Protecting Routes

You should ensure that any route that performs an action which requires recent password confirmation is assigned the `password.confirm` middleware. This middleware is included with the default installation of Laravel and will automatically store the user's intended destination in the session so that the user may be redirected to that location after confirming their password. After storing the user's intended destination in the session, the middleware will redirect the user to the `password.confirm` [named route](/docs/{{version}}/routing#named-routes):

    Route::get('/settings', function () {
        // ...
    })->middleware(['password.confirm']);

    Route::post('/settings', function () {
        // ...
    })->middleware(['password.confirm']);

<a name="adding-custom-guards"></a>
## Adding Custom Guards

You may define your own authentication guards using the `extend` method on the `Auth` facade. You should place your call to the `extend` method within a [service provider](/docs/{{version}}/providers). Since Laravel already ships with an `AppServiceProvider`, we can place the code in that provider:

    <?php

    namespace App\Providers;

    use App\Services\Auth\JwtGuard;
    use Illuminate\Contracts\Foundation\Application;
    use Illuminate\Support\Facades\Auth;
    use Illuminate\Support\ServiceProvider;

    class AppServiceProvider extends ServiceProvider
    {
        // ...

        /**
         * Bootstrap any application services.
         */
        public function boot(): void
        {
            Auth::extend('jwt', function (Application $app, string $name, array $config) {
                // Return an instance of Illuminate\Contracts\Auth\Guard...

                return new JwtGuard(Auth::createUserProvider($config['provider']));
            });
        }
    }

As you can see in the example above, the callback passed to the `extend` method should return an implementation of `Illuminate\Contracts\Auth\Guard`. This interface contains a few methods you will need to implement to define a custom guard. Once your custom guard has been defined, you may reference the guard in the `guards` configuration of your `auth.php` configuration file:

    'guards' => [
        'api' => [
            'driver' => 'jwt',
            'provider' => 'users',
        ],
    ],

<a name="closure-request-guards"></a>
### Closure Request Guards

The simplest way to implement a custom, HTTP request based authentication system is by using the `Auth::viaRequest` method. This method allows you to quickly define your authentication process using a single closure.

To get started, call the `Auth::viaRequest` method within the `boot` method of your application's `AppServiceProvider`. The `viaRequest` method accepts an authentication driver name as its first argument. This name can be any string that describes your custom guard. The second argument passed to the method should be a closure that receives the incoming HTTP request and returns a user instance or, if authentication fails, `null`:

    use App\Models\User;
    use Illuminate\Http\Request;
    use Illuminate\Support\Facades\Auth;

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        Auth::viaRequest('custom-token', function (Request $request) {
            return User::where('token', (string) $request->token)->first();
        });
    }

Once your custom authentication driver has been defined, you may configure it as a driver within the `guards` configuration of your `auth.php` configuration file:

    'guards' => [
        'api' => [
            'driver' => 'custom-token',
        ],
    ],

Finally, you may reference the guard when assigning the authentication middleware to a route:

    Route::middleware('auth:api')->group(function () {
        // ...
    });

<a name="adding-custom-user-providers"></a>
## Adding Custom User Providers

If you are not using a traditional relational database to store your users, you will need to extend Laravel with your own authentication user provider. We will use the `provider` method on the `Auth` facade to define a custom user provider. The user provider resolver should return an implementation of `Illuminate\Contracts\Auth\UserProvider`:

    <?php

    namespace App\Providers;

    use App\Extensions\MongoUserProvider;
    use Illuminate\Contracts\Foundation\Application;
    use Illuminate\Support\Facades\Auth;
    use Illuminate\Support\ServiceProvider;

    class AppServiceProvider extends ServiceProvider
    {
        // ...

        /**
         * Bootstrap any application services.
         */
        public function boot(): void
        {
            Auth::provider('mongo', function (Application $app, array $config) {
                // Return an instance of Illuminate\Contracts\Auth\UserProvider...

                return new MongoUserProvider($app->make('mongo.connection'));
            });
        }
    }

After you have registered the provider using the `provider` method, you may switch to the new user provider in your `auth.php` configuration file. First, define a `provider` that uses your new driver:

    'providers' => [
        'users' => [
            'driver' => 'mongo',
        ],
    ],

Finally, you may reference this provider in your `guards` configuration:

    'guards' => [
        'web' => [
            'driver' => 'session',
            'provider' => 'users',
        ],
    ],

<a name="the-user-provider-contract"></a>
### The User Provider Contract

`Illuminate\Contracts\Auth\UserProvider` implementations are responsible for fetching an `Illuminate\Contracts\Auth\Authenticatable` implementation out of a persistent storage system, such as MySQL, MongoDB, etc. These two interfaces allow the Laravel authentication mechanisms to continue functioning regardless of how the user data is stored or what type of class is used to represent the authenticated user:

Let's take a look at the `Illuminate\Contracts\Auth\UserProvider` contract:

    <?php

    namespace Illuminate\Contracts\Auth;

    interface UserProvider
    {
        public function retrieveById($identifier);
        public function retrieveByToken($identifier, $token);
        public function updateRememberToken(Authenticatable $user, $token);
        public function retrieveByCredentials(array $credentials);
        public function validateCredentials(Authenticatable $user, array $credentials);
        public function rehashPasswordIfRequired(Authenticatable $user, array $credentials, bool $force = false);
    }

The `retrieveById` function typically receives a key representing the user, such as an auto-incrementing ID from a MySQL database. The `Authenticatable` implementation matching the ID should be retrieved and returned by the method.

The `retrieveByToken` function retrieves a user by their unique `$identifier` and "remember me" `$token`, typically stored in a database column like `remember_token`. As with the previous method, the `Authenticatable` implementation with a matching token value should be returned by this method.

The `updateRememberToken` method updates the `$user` instance's `remember_token` with the new `$token`. A fresh token is assigned to users on a successful "remember me" authentication attempt or when the user is logging out.

The `retrieveByCredentials` method receives the array of credentials passed to the `Auth::attempt` method when attempting to authenticate with an application. The method should then "query" the underlying persistent storage for the user matching those credentials. Typically, this method will run a query with a "where" condition that searches for a user record with a "username" matching the value of `$credentials['username']`. The method should return an implementation of `Authenticatable`. **This method should not attempt to do any password validation or authentication.**

The `validateCredentials` method should compare the given `$user` with the `$credentials` to authenticate the user. For example, this method will typically use the `Hash::check` method to compare the value of `$user->getAuthPassword()` to the value of `$credentials['password']`. This method should return `true` or `false` indicating whether the password is valid.

The `rehashPasswordIfRequired` method should rehash the given `$user`'s password if required and supported. For example, this method will typically use the `Hash::needsRehash` method to determine if the `$credentials['password']` value needs to be rehashed. If the password needs to be rehashed, the method should use the `Hash::make` method to rehash the password and update the user's record in the underlying persistent storage.

<a name="the-authenticatable-contract"></a>
### The Authenticatable Contract

Now that we have explored each of the methods on the `UserProvider`, let's take a look at the `Authenticatable` contract. Remember, user providers should return implementations of this interface from the `retrieveById`, `retrieveByToken`, and `retrieveByCredentials` methods:

    <?php

    namespace Illuminate\Contracts\Auth;

    interface Authenticatable
    {
        public function getAuthIdentifierName();
        public function getAuthIdentifier();
        public function getAuthPasswordName();
        public function getAuthPassword();
        public function getRememberToken();
        public function setRememberToken($value);
        public function getRememberTokenName();
    }

This interface is simple. The `getAuthIdentifierName` method should return the name of the "primary key" column for the user and the `getAuthIdentifier` method should return the "primary key" of the user. When using a MySQL back-end, this would likely be the auto-incrementing primary key assigned to the user record. The `getAuthPasswordName` method should return the name of the user's password column. The `getAuthPassword` method should return the user's hashed password.

This interface allows the authentication system to work with any "user" class, regardless of what ORM or storage abstraction layer you are using. By default, Laravel includes an `App\Models\User` class in the `app/Models` directory which implements this interface.

<a name="automatic-password-rehashing"></a>
## Automatic Password Rehashing

Laravel's default password hashing algorithm is bcrypt. The "work factor" for bcrypt hashes can be adjusted via your application's `config/hashing.php` configuration file or the `BCRYPT_ROUNDS` environment variable.

Typically, the bcrypt work factor should be increased over time as CPU / GPU processing power increases. If you increase the bcrypt work factor for your application, Laravel will gracefully and automatically rehash user passwords as users authenticate with your application via Laravel's starter kits or when you [manually authenticate users](#authenticating-users) via the `attempt` method.

Typically, automatic password rehashing should not disrupt your application; however, you may disable this behavior by publishing the `hashing` configuration file:

```shell
php artisan config:publish hashing
```

Once the configuration file has been published, you may set the `rehash_on_login` configuration value to `false`:

```php
'rehash_on_login' => false,
```

<a name="events"></a>
## Events

Laravel dispatches a variety of [events](/docs/{{version}}/events) during the authentication process. You may [define listeners](/docs/{{version}}/events) for any of the following events:

<div class="overflow-auto">

| Event Name |
| --- |
| `Illuminate\Auth\Events\Registered` |
| `Illuminate\Auth\Events\Attempting` |
| `Illuminate\Auth\Events\Authenticated` |
| `Illuminate\Auth\Events\Login` |
| `Illuminate\Auth\Events\Failed` |
| `Illuminate\Auth\Events\Validated` |
| `Illuminate\Auth\Events\Verified` |
| `Illuminate\Auth\Events\Logout` |
| `Illuminate\Auth\Events\CurrentDeviceLogout` |
| `Illuminate\Auth\Events\OtherDeviceLogout` |
| `Illuminate\Auth\Events\Lockout` |
| `Illuminate\Auth\Events\PasswordReset` |

</div>
