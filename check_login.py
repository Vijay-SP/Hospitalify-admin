from flask import session, redirect, request, url_for
import functools

#function to check the logged in status. Add this before every route(except home route)
def check_login(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if ("user" not in session):
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)
    return secure_function