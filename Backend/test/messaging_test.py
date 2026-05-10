"""
Messaging and key-management tests for the FastAPI backend.

Covers the five endpoints that the frontend relies on but had no test coverage:

    GET  /aes-keys/                         – retrieve AES key
    GET  /keys/users/{user_id}/public-key   – fetch another user's public key
    GET  /keys/me/public-key                – fetch own public key
    POST /messages/                         – send an encrypted message
    GET  /messages/?user={userId}           – fetch conversation messages (both directions)

Socket.IO emission inside POST /messages/ is patched so no real socket server
is needed during tests.
"""

import os

os.environ["JWT_SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from unittest.mock import AsyncMock, patch
import pytest

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from db.session import get_db
from models.user_model import User
from models.aes_keys_model import AesKeys
from models.mess_model import Message
from endpoints.auth import pwd_context, create_jwt_token, secret_key_generator

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Sentinel so callers can pass public_key=None explicitly without the helper
# substituting the default [1, 2, 3].
_MISSING = object()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_user(
    session: Session,
    email: str = "user@example.com",
    password: str = "password123",
    public_key=_MISSING,  # pass None explicitly for "no public key"
) -> tuple[User, str]:
    """Insert a user and return (user, bearer_token).

    Omit ``public_key`` to get a default ``[1, 2, 3]`` key.
    Pass ``public_key=None`` to create a user with no public key stored.
    """
    otp_secret = secret_key_generator()
    resolved_key = [1, 2, 3] if public_key is _MISSING else public_key
    user = User(
        email=email,
        name="Test User",
        password=pwd_context.hash(password),
        otp_secret=otp_secret,
        public_key=resolved_key,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_jwt_token({
        "sub_id": user.id,
        "sub_admin": False,
        "sub_email": user.email,
    })
    return user, token


def _store_aes_key(session: Session, user_id: str, aes_key: str = "deadbeef" * 4) -> AesKeys:
    key = AesKeys(user_id=user_id, aes_key=aes_key)
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


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


# ── GET /aes-keys/ ────────────────────────────────────────────────────────────

class TestGetAesKey:
    def test_unauthenticated_request_rejected(self, client):
        res = client.get("/aes-keys/")
        assert res.status_code == 403

    def test_returns_404_when_no_key_stored(self, client, db_session):
        _, token = _create_user(db_session)
        res = client.get("/aes-keys/", headers=_auth(token))
        assert res.status_code == 404

    def test_returns_aes_key_for_authenticated_user(self, client, db_session):
        user, token = _create_user(db_session)
        _store_aes_key(db_session, user.id, aes_key="cafebabe" * 4)

        res = client.get("/aes-keys/", headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["aes_key"] == "cafebabe" * 4

    def test_response_contains_only_aes_key_field(self, client, db_session):
        """Main branch response model exposes only aes_key, not user_id."""
        user, token = _create_user(db_session)
        _store_aes_key(db_session, user.id, aes_key="aabbccdd")

        body = client.get("/aes-keys/", headers=_auth(token)).json()
        assert "aes_key" in body
        assert "user_id" not in body

    def test_returns_own_key_not_another_users(self, client, db_session):
        user_a, token_a = _create_user(db_session, email="a@example.com")
        user_b, _       = _create_user(db_session, email="b@example.com")
        _store_aes_key(db_session, user_a.id, aes_key="keyforA0")
        _store_aes_key(db_session, user_b.id, aes_key="keyforB0")

        res = client.get("/aes-keys/", headers=_auth(token_a))
        assert res.json()["aes_key"] == "keyforA0"


# ── GET /keys/users/{user_id}/public-key ─────────────────────────────────────

class TestGetOtherUsersPublicKey:
    def test_unauthenticated_request_rejected(self, client, db_session):
        user, _ = _create_user(db_session)
        res = client.get(f"/keys/users/{user.id}/public-key")
        assert res.status_code == 403

    def test_returns_public_key_for_existing_user(self, client, db_session):
        target, _      = _create_user(db_session, email="target@example.com", public_key=[10, 20, 30])
        requester, tok = _create_user(db_session, email="requester@example.com")

        res = client.get(f"/keys/users/{target.id}/public-key", headers=_auth(tok))
        assert res.status_code == 200
        assert res.json()["publicKey"] == [10, 20, 30]

    def test_returns_404_for_nonexistent_user(self, client, db_session):
        _, token = _create_user(db_session)
        res = client.get("/keys/users/no-such-user/public-key", headers=_auth(token))
        assert res.status_code == 404

    def test_returns_404_when_user_has_no_public_key(self, client, db_session):
        target, _      = _create_user(db_session, email="nopub@example.com", public_key=None)
        requester, tok = _create_user(db_session, email="req@example.com")

        res = client.get(f"/keys/users/{target.id}/public-key", headers=_auth(tok))
        assert res.status_code == 404


# ── GET /keys/me/public-key ───────────────────────────────────────────────────

class TestGetMyPublicKey:
    def test_unauthenticated_request_rejected(self, client):
        res = client.get("/keys/me/public-key")
        assert res.status_code == 403

    def test_returns_own_public_key(self, client, db_session):
        user, token = _create_user(db_session, public_key=[7, 8, 9])
        res = client.get("/keys/me/public-key", headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["publicKey"] == [7, 8, 9]

    def test_returns_404_when_no_public_key(self, client, db_session):
        user, token = _create_user(db_session, public_key=None)
        res = client.get("/keys/me/public-key", headers=_auth(token))
        assert res.status_code == 404


# ── POST /messages/ ───────────────────────────────────────────────────────────

class TestSendMessage:
    """
    The endpoint calls sio_server.emit() internally.  We patch it so tests
    do not need a running Socket.IO server.
    """

    @pytest.fixture(autouse=True)
    def _patch_socket(self):
        with patch("endpoints.mess.sio_server.emit", new_callable=AsyncMock):
            yield

    def test_unauthenticated_request_rejected(self, client, db_session):
        _, _ = _create_user(db_session)
        res = client.post("/messages/", json={"receiver": "anyone", "message": "hi"})
        assert res.status_code == 403

    def test_send_message_returns_sent_status_and_id(self, client, db_session):
        sender, token = _create_user(db_session, email="sender@example.com")
        receiver, _   = _create_user(db_session, email="receiver@example.com")

        res = client.post(
            "/messages/",
            json={"receiver": receiver.id, "message": "encrypted-payload"},
            headers=_auth(token),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "sent"
        assert "id" in body

    def test_message_is_persisted_in_db(self, client, db_session):
        sender, token = _create_user(db_session, email="sender@example.com")
        receiver, _   = _create_user(db_session, email="receiver@example.com")

        client.post(
            "/messages/",
            json={"receiver": receiver.id, "message": "encrypted-payload"},
            headers=_auth(token),
        )
        msg = db_session.get(Message, 1)
        assert msg is not None
        assert msg.sender == sender.id
        assert msg.receiver == receiver.id
        assert msg.encrypted_msg == "encrypted-payload"

    def test_missing_receiver_field_rejected(self, client, db_session):
        _, token = _create_user(db_session)
        res = client.post(
            "/messages/",
            json={"message": "encrypted-payload"},
            headers=_auth(token),
        )
        assert res.status_code == 422

    def test_missing_message_field_rejected(self, client, db_session):
        _, token = _create_user(db_session)
        res = client.post(
            "/messages/",
            json={"receiver": "someone"},
            headers=_auth(token),
        )
        assert res.status_code == 422


# ── GET /messages/?user={userId} ─────────────────────────────────────────────

class TestGetMessages:
    """
    GET /messages/ requires authentication and returns messages in both
    directions between the authenticated user and the given ``user`` parameter.
    """

    @pytest.fixture(autouse=True)
    def _patch_socket(self):
        with patch("endpoints.mess.sio_server.emit", new_callable=AsyncMock):
            yield

    def _seed_message(self, session: Session, sender_id: str, receiver_id: str, text: str = "msg") -> Message:
        msg = Message(sender=sender_id, receiver=receiver_id, encrypted_msg=text)
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg

    def test_unauthenticated_request_rejected(self, client, db_session):
        user, _ = _create_user(db_session)
        res = client.get(f"/messages/?user={user.id}")
        assert res.status_code == 403

    def test_returns_empty_list_when_no_messages(self, client, db_session):
        user_a, token_a = _create_user(db_session, email="a@example.com")
        user_b, _       = _create_user(db_session, email="b@example.com")

        res = client.get(f"/messages/?user={user_b.id}", headers=_auth(token_a))
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_messages_sent_by_authenticated_user(self, client, db_session):
        user_a, token_a = _create_user(db_session, email="a@example.com")
        user_b, _       = _create_user(db_session, email="b@example.com")
        self._seed_message(db_session, user_a.id, user_b.id, "hello from a")

        res = client.get(f"/messages/?user={user_b.id}", headers=_auth(token_a))
        assert res.status_code == 200
        msgs = res.json()
        assert len(msgs) == 1
        assert msgs[0]["encrypted_msg"] == "hello from a"

    def test_returns_messages_received_by_authenticated_user(self, client, db_session):
        user_a, token_a = _create_user(db_session, email="a@example.com")
        user_b, _       = _create_user(db_session, email="b@example.com")
        self._seed_message(db_session, user_b.id, user_a.id, "hello from b")

        res = client.get(f"/messages/?user={user_b.id}", headers=_auth(token_a))
        assert res.status_code == 200
        msgs = res.json()
        assert len(msgs) == 1
        assert msgs[0]["encrypted_msg"] == "hello from b"

    def test_returns_full_conversation_in_both_directions(self, client, db_session):
        user_a, token_a = _create_user(db_session, email="a@example.com")
        user_b, _       = _create_user(db_session, email="b@example.com")
        self._seed_message(db_session, user_a.id, user_b.id, "msg1")
        self._seed_message(db_session, user_b.id, user_a.id, "msg2")
        self._seed_message(db_session, user_a.id, user_b.id, "msg3")

        res = client.get(f"/messages/?user={user_b.id}", headers=_auth(token_a))
        assert res.status_code == 200
        texts = [m["encrypted_msg"] for m in res.json()]
        assert texts == ["msg1", "msg2", "msg3"]

    def test_does_not_return_messages_for_unrelated_conversation(self, client, db_session):
        user_a, token_a = _create_user(db_session, email="a@example.com")
        user_b, _       = _create_user(db_session, email="b@example.com")
        user_c, _       = _create_user(db_session, email="c@example.com")
        self._seed_message(db_session, user_b.id, user_c.id, "for-c")

        res = client.get(f"/messages/?user={user_b.id}", headers=_auth(token_a))
        assert res.json() == []

    def test_after_parameter_filters_old_messages(self, client, db_session):
        user_a, token_a = _create_user(db_session, email="a@example.com")
        user_b, _       = _create_user(db_session, email="b@example.com")
        msg1 = self._seed_message(db_session, user_a.id, user_b.id, "old")
        self._seed_message(db_session, user_a.id, user_b.id, "new")

        res = client.get(f"/messages/?user={user_b.id}&after={msg1.id}", headers=_auth(token_a))
        assert res.status_code == 200
        msgs = res.json()
        assert len(msgs) == 1
        assert msgs[0]["encrypted_msg"] == "new"

    def test_missing_user_param_returns_422(self, client, db_session):
        _, token = _create_user(db_session)
        res = client.get("/messages/", headers=_auth(token))
        assert res.status_code == 422

    def test_each_message_contains_expected_fields(self, client, db_session):
        user_a, token_a = _create_user(db_session, email="a@example.com")
        user_b, _       = _create_user(db_session, email="b@example.com")
        self._seed_message(db_session, user_a.id, user_b.id, "payload")

        msg = client.get(f"/messages/?user={user_b.id}", headers=_auth(token_a)).json()[0]
        assert "id" in msg
        assert "sender" in msg
        assert "receiver" in msg
        assert "encrypted_msg" in msg
        assert msg["sender"] == user_a.id
        assert msg["receiver"] == user_b.id
