import os

os.environ["JWT_SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
import pyotp
from urllib.parse import urlparse, parse_qs

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from db.session import get_db
from models.user_model import User
from endpoints.auth import pwd_context, secret_key_generator

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def _create_user(
    session: Session,
    email: str = "user@example.com",
    password: str = "password123",
) -> tuple[User, str]:
    otp_secret = secret_key_generator()
    user = User(
        email=email,
        name="Test User",
        password=pwd_context.hash(password),
        otp_secret=otp_secret,
        public_key=[1, 2, 3],
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, otp_secret


@pytest.fixture(autouse=True)
def _reset_db():
    SQLModel.metadata.create_all(_test_engine)
    yield
    SQLModel.metadata.drop_all(_test_engine)


@pytest.fixture()
def db_session(_reset_db):
    with Session(_test_engine) as session:
        yield session


@pytest.fixture()
def client(db_session):
    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Signup ────────────────────────────────────────────────────────────────────

def test_signup_fail_email(client, db_session):
    _create_user(db_session, email="alice@example.com")
    response = client.post("/users/signup", json={
        "name": "alice notbob",
        "email": "alice@example.com",
        "password": "alice123",
        "public_key": [1, 2, 3],
    })
    assert response.status_code == 400


def test_signup_fail_password(client):
    response = client.post("/users/signup", json={
        "name": "alice notbob",
        "email": "alice@example.dk",
        "password": "alice",
        "public_key": [1, 2, 3],
    })
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "String should have at least 8 characters"


def test_signup_success(client):
    response = client.post("/users/signup", json={
        "name": "alice notbob",
        "email": "thisisalice@sparta.com",
        "password": "alice123",
        "public_key": [1, 2, 3],
    })
    assert response.status_code == 200
    assert "totp_uri" in response.json()


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login(client, db_session):
    _create_user(db_session, email="alice@example.com", password="alice123")
    response = client.post("/auth/login", json={
        "email": "alice@example.com",
        "password": "alice123",
    })
    assert response.status_code == 200


# ── OTP Verification ──────────────────────────────────────────────────────────

def test_otp_verification(client, db_session):
    _, otp_secret = _create_user(db_session, email="alice@example.com")
    valid_otp = pyotp.TOTP(otp_secret).now()
    response = client.post("/auth/verify-otp", json={
        "email": "alice@example.com",
        "otp": valid_otp,
    })
    assert response.status_code == 200
    body = response.json()
    assert "token" in body
    assert body["token_type"] == "bearer"


# ── End-to-end flow ───────────────────────────────────────────────────────────

def test_full_signup_login_otp_flow(client):
    signup_res = client.post("/users/signup", json={
        "name": "alice notbob",
        "email": "thisisalice@sparta.com",
        "password": "alice123",
        "public_key": [1, 2, 3],
    })
    assert signup_res.status_code == 200
    totp_uri = signup_res.json()["totp_uri"]
    otp_secret = parse_qs(urlparse(totp_uri).query)["secret"][0]

    login_res = client.post("/auth/login", json={
        "email": "thisisalice@sparta.com",
        "password": "alice123",
    })
    assert login_res.status_code == 200

    valid_otp = pyotp.TOTP(otp_secret).now()
    otp_res = client.post("/auth/verify-otp", json={
        "email": "thisisalice@sparta.com",
        "otp": valid_otp,
    })
    assert otp_res.status_code == 200
    assert "token" in otp_res.json()
