"""前端 API 封装：统一调用后端 REST API，管理登录态（cookie）。

使用 requests.Session 自动维护 cookie，登录后后续请求自动携带 session。
"""

import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000"


def get_session() -> requests.Session:
    """获取（或创建）共享的 requests.Session，自动维护 cookie。"""
    if "http_session" not in st.session_state:
        st.session_state["http_session"] = requests.Session()
    return st.session_state["http_session"]


def request(method: str, path: str, json_body=None, params=None):
    """统一请求，返回 (status_code, body_dict)。"""
    s = get_session()
    try:
        resp = s.request(method, BASE_URL + path, json=json_body, params=params, timeout=10)
        return resp.status_code, resp.json()
    except requests.RequestException as exc:
        return 500, {"code": 500, "msg": f"无法连接后端：{exc}", "data": None}


def login(username: str, password: str):
    """登录，成功后记录登录态。"""
    status, body = request("POST", "/api/auth/login", json_body={"username": username, "password": password})
    if status == 200:
        st.session_state["logged_in"] = True
        st.session_state["user"] = body["data"]
    return status, body


def logout():
    """登出并清除本地登录态。"""
    request("POST", "/api/auth/logout")
    get_session().cookies.clear()
    st.session_state["logged_in"] = False
    st.session_state.pop("user", None)


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def current_user():
    return st.session_state.get("user")
