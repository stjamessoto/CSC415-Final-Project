import os
import datetime
import functools
import streamlit as st
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "retaillang-dev-secret")
ALGORITHM  = "HS256"
TOKEN_TTL  = datetime.timedelta(hours=8)

DEMO_USERS = {
    "admin":   os.getenv("ADMIN_PASSWORD", "retail123"),
    "analyst": os.getenv("ANALYST_PASSWORD", "analyst123"),
    "demo":    os.getenv("DEMO_PASSWORD", "demo"),
}


def generate_token(username: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + TOKEN_TTL,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def authenticate(username: str, password: str) -> bool:
    return DEMO_USERS.get(username) == password


def login_wall():
    """
    Renders a login form and blocks the app until the user is authenticated.
    Call this at the top of app.py before any other rendering.
    """
    if "auth_token" in st.session_state:
        payload = verify_token(st.session_state["auth_token"])
        if payload:
            return payload["sub"]
        else:
            del st.session_state["auth_token"]
            st.warning("Session expired. Please log in again.")

    st.title("RetailLang IDE")
    st.subheader("Sign in")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
        if authenticate(username, password):
            token = generate_token(username)
            st.session_state["auth_token"] = token
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.caption("Demo credentials — admin / retail123  ·  demo / demo")
    st.stop()


def logout():
    if "auth_token" in st.session_state:
        del st.session_state["auth_token"]
    st.rerun()


def require_auth(func):
    """Decorator: wraps a page function with login_wall."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        login_wall()
        return func(*args, **kwargs)
    return wrapper