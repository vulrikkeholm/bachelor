"""
Authentication tests for the FastAPI backend.

Runs against an isolated in-memory SQLite database — no external services needed.
"""

import os

# Must be set before any application modules are imported so that module-level
# code (e.g. engine creation in db/session.py) picks up the test values.
os.environ["JWT_SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import jwt
import pytest
import pyotp
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from db.session import get_db
from models.user_model import User
from endpoints.auth import pwd_context, create_jwt_token, secret_key_generator

_JWT_SECRET = os.environ["JWT_SECRET_KEY"]
_JWT_ALGORITHM = os.environ["JWT_ALGORITHM"]

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_user(
    session: Session,
    email: str = "user@example.com",
    password: str = "password123",
    admin: str = "False",
) -> tuple[User, str]:
    """Insert a user directly into the test DB and return (user, otp_secret)."""
    otp_secret = secret_key_generator()
    user = User(
        email=email,
        name="Test User",
        password=pwd_context.hash(password),
        otp_secret=otp_secret,
        admin=admin,
        public_key=[1, 2, 3],
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, otp_secret


# ── Fixtures ──────────────────────────────────────────────────────────────────

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

class TestSignup:
    def test_valid_signup_returns_totp_uri(self, client):
        res = client.post("/users/signup", json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "alicepassword",
            "public_key": [1, 2, 3],
        })
        assert res.status_code == 200
        data = res.json()
        assert "totp_uri" in data
        assert "otpauth://" in data["totp_uri"]

    def test_duplicate_email_rejected(self, client, db_session):
        _create_user(db_session, email="alice@example.com")
        res = client.post("/users/signup", json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "alicepassword",
            "public_key": [1, 2, 3],
        })
        assert res.status_code == 400
        assert "already registered" in res.json()["detail"].lower()

    def test_short_password_rejected(self, client):
        res = client.post("/users/signup", json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "short",
            "public_key": [1, 2, 3],
        })
        assert res.status_code == 422

    def test_missing_required_fields_rejected(self, client):
        res = client.post("/users/signup", json={"name": "Alice"})
        assert res.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_valid_credentials_accepted(self, client, db_session):
        _create_user(db_session, email="user@example.com", password="mypassword")
        res = client.post("/auth/login", json={
            "email": "user@example.com",
            "password": "mypassword",
        })
        assert res.status_code == 200
        assert "message" in res.json()

    def test_wrong_password_rejected(self, client, db_session):
        _create_user(db_session, email="user@example.com", password="mypassword")
        res = client.post("/auth/login", json={
            "email": "user@example.com",
            "password": "wrongpassword",
        })
        assert res.status_code == 401

    def test_unknown_email_rejected(self, client):
        res = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "password123",
        })
        assert res.status_code == 401

    def test_missing_email_field_rejected(self, client):
        res = client.post("/auth/login", json={"password": "password123"})
        assert res.status_code == 422

    def test_missing_password_field_rejected(self, client):
        res = client.post("/auth/login", json={"email": "user@example.com"})
        assert res.status_code == 422


# ── OTP Verification ──────────────────────────────────────────────────────────

class TestOtpVerification:
    def test_valid_otp_returns_bearer_token(self, client, db_session):
        _, otp_secret = _create_user(db_session, email="user@example.com")
        valid_otp = pyotp.TOTP(otp_secret).now()
        res = client.post("/auth/verify-otp", json={
            "email": "user@example.com",
            "otp": valid_otp,
        })
        assert res.status_code == 200
        body = res.json()
        assert "token" in body
        assert body["token_type"] == "bearer"
        assert "user_id" in body

    def test_returned_token_contains_correct_claims(self, client, db_session):
        user, otp_secret = _create_user(db_session, email="user@example.com")
        valid_otp = pyotp.TOTP(otp_secret).now()
        res = client.post("/auth/verify-otp", json={
            "email": "user@example.com",
            "otp": valid_otp,
        })
        token = res.json()["token"]
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        assert payload["sub_email"] == "user@example.com"
        assert payload["sub_id"] == user.id
        assert payload["sub_admin"] is False

    def test_invalid_otp_rejected(self, client, db_session):
        _create_user(db_session, email="user@example.com")
        res = client.post("/auth/verify-otp", json={
            "email": "user@example.com",
            "otp": "000000",
        })
        assert res.status_code == 401

    def test_unknown_email_returns_404(self, client):
        res = client.post("/auth/verify-otp", json={
            "email": "nobody@example.com",
            "otp": "123456",
        })
        assert res.status_code == 404


# ── JWT validation (exercised through a protected endpoint) ───────────────────

class TestJwtValidation:
    _PROTECTED = "/keys/me/public-key"

    def test_valid_token_grants_access(self, client, db_session):
        user, _ = _create_user(db_session)
        token = create_jwt_token({
            "sub_id": user.id,
            "sub_admin": False,
            "sub_email": user.email,
        })
        res = client.get(self._PROTECTED, headers={"Authorization": f"Bearer {token}"})
        # 401/403 would indicate the JWT was rejected; any other code means auth passed
        assert res.status_code not in (401, 403)

    def test_missing_auth_header_returns_403(self, client):
        res = client.get(self._PROTECTED)
        assert res.status_code == 403

    def test_malformed_token_rejected(self, client):
        res = client.get(self._PROTECTED, headers={"Authorization": "Bearer not.a.valid.token"})
        assert res.status_code == 401

    def test_expired_token_rejected(self, client, db_session):
        user, _ = _create_user(db_session)
        expired_token = jwt.encode(
            {
                "sub_id": user.id,
                "sub_admin": False,
                "sub_email": user.email,
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            _JWT_SECRET,
            algorithm=_JWT_ALGORITHM,
        )
        res = client.get(self._PROTECTED, headers={"Authorization": f"Bearer {expired_token}"})
        assert res.status_code == 401

    def test_token_signed_with_wrong_secret_rejected(self, client, db_session):
        user, _ = _create_user(db_session)
        bad_token = jwt.encode(
            {
                "sub_id": user.id,
                "sub_admin": False,
                "sub_email": user.email,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "completely-wrong-secret",
            algorithm=_JWT_ALGORITHM,
        )
        res = client.get(self._PROTECTED, headers={"Authorization": f"Bearer {bad_token}"})
        assert res.status_code == 401

    def test_tampered_token_rejected(self, client, db_session):
        user, _ = _create_user(db_session)
        token = create_jwt_token({
            "sub_id": user.id,
            "sub_admin": False,
            "sub_email": user.email,
        })
        tampered = token[:-4] + "XXXX"
        res = client.get(self._PROTECTED, headers={"Authorization": f"Bearer {tampered}"})
        assert res.status_code == 401

    def test_token_missing_sub_email_rejected(self, client, db_session):
        user, _ = _create_user(db_session)
        token = jwt.encode(
            {
                "sub_id": user.id,
                "sub_admin": False,
                # sub_email intentionally omitted
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            _JWT_SECRET,
            algorithm=_JWT_ALGORITHM,
        )
        res = client.get(self._PROTECTED, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401

    def test_token_with_elevated_admin_claim_rejected(self, client, db_session):
        user, _ = _create_user(db_session, admin="False")
        # Token claims admin=True but the DB record says admin="False"
        token = jwt.encode(
            {
                "sub_id": user.id,
                "sub_admin": True,
                "sub_email": user.email,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            _JWT_SECRET,
            algorithm=_JWT_ALGORITHM,
        )
        res = client.get(self._PROTECTED, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 418


# ── End-to-end flow ───────────────────────────────────────────────────────────

class TestFullAuthFlow:
    def test_signup_login_otp_then_protected_endpoint(self, client):
        # 1. Signup
        signup_res = client.post("/users/signup", json={
            "name": "Bob",
            "email": "bob@example.com",
            "password": "bobpassword1",
            "public_key": [10, 20, 30],
        })
        assert signup_res.status_code == 200
        totp_uri = signup_res.json()["totp_uri"]
        otp_secret = parse_qs(urlparse(totp_uri).query)["secret"][0]

        # 2. Login
        login_res = client.post("/auth/login", json={
            "email": "bob@example.com",
            "password": "bobpassword1",
        })
        assert login_res.status_code == 200

        # 3. OTP verification → JWT token
        valid_otp = pyotp.TOTP(otp_secret).now()
        otp_res = client.post("/auth/verify-otp", json={
            "email": "bob@example.com",
            "otp": valid_otp,
        })
        assert otp_res.status_code == 200
        token = otp_res.json()["token"]

        # 4. Use token on a protected endpoint
        protected_res = client.get(
            "/keys/me/public-key",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert protected_res.status_code not in (401, 403)
