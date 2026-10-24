"""
The EmailNotifier against a stand-in for smtplib that records what it is asked to do, so it
checks how the adapter talks to an SMTP server (encryption, login, message) without one.
"""
import pytest

from omnis.adapters import EmailNotifier
from omnis.adapters.notifier import email_notifier


class RecordingSmtp:
    """Stands in for smtplib.SMTP and smtplib.SMTP_SSL, recording each connection."""

    connections: list["RecordingSmtp"] = []

    def __init__(self, host, port, context=None, timeout=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.implicit_tls = context is not None
        self.calls: list[tuple] = []
        RecordingSmtp.connections.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.calls.append(("quit",))

    def starttls(self, context=None):
        self.calls.append(("starttls",))

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def send_message(self, message):
        self.calls.append(("send", message))


@pytest.fixture
def smtp(monkeypatch):
    RecordingSmtp.connections = []
    monkeypatch.setattr(email_notifier.smtplib, "SMTP", RecordingSmtp)
    monkeypatch.setattr(email_notifier.smtplib, "SMTP_SSL", RecordingSmtp)
    return RecordingSmtp


def make_notifier(port: int) -> EmailNotifier:
    return EmailNotifier(host="smtp.gmail.com", port=port, user="omnis@gmail.com", password="app password", to="me@example.com")


def test_e_mails_a_failure_with_its_details(smtp):
    """
    Checks: a failure is sent as one e-mail from the SMTP account to the recipient, with the flow
    in the subject and the run, the reason and the last task in the body.

    If it fails: failure e-mails would not arrive, arrive to the wrong address, or not say which flow
    and run failed, so whoever gets them couldn't find the failure in Airflow.
    """
    make_notifier(587).notify_failure("health", "scheduled__2026-10-24T13:00:00+00:00", "task_failure", "orig.series_gimnasio")

    [(_, message)] = [call for call in smtp.connections[0].calls if call[0] == "send"]
    assert message["From"] == "omnis@gmail.com"
    assert message["To"] == "me@example.com"
    assert message["Subject"] == "Omnis: the health flow failed"
    body = message.get_content()
    assert "scheduled__2026-10-24T13:00:00+00:00" in body
    assert "task_failure" in body
    assert "orig.series_gimnasio" in body


def test_without_last_task_the_e_mail_does_not_mention_it(smtp):
    """
    Checks: when the orchestrator doesn't know the last task, the e-mail still goes and says nothing
    about it.

    If it fails: a failure without last task would crash the notifier (no e-mail at all) or print
    "None" as if it were a task.
    """
    make_notifier(587).notify_failure("health", "run_1", "task_failure", None)

    [(_, message)] = [call for call in smtp.connections[0].calls if call[0] == "send"]
    assert "last task" not in message.get_content()
    assert "None" not in message.get_content()


def test_port_587_encrypts_with_starttls_before_logging_in(smtp):
    """
    Checks: on any port but 465, the connection is upgraded with STARTTLS before logging in, then
    the e-mail is sent and the connection closed.

    If it fails: the password would travel unencrypted, or servers like Gmail would reject the login
    (they require encryption first), so no failure e-mail would ever arrive.
    """
    make_notifier(587).notify_failure("health", "run_1", "task_failure", None)

    [connection] = smtp.connections
    assert (connection.host, connection.port, connection.implicit_tls) == ("smtp.gmail.com", 587, False)
    assert [call[0] for call in connection.calls] == ["starttls", "login", "send", "quit"]
    assert connection.calls[1] == ("login", "omnis@gmail.com", "app password")


def test_port_465_uses_implicit_tls(smtp):
    """
    Checks: on port 465 the connection is encrypted from the start (SMTP over TLS), without STARTTLS.

    If it fails: a server configured on 465 would never answer a plain connection, and no failure
    e-mail would arrive.
    """
    make_notifier(465).notify_failure("health", "run_1", "task_failure", None)

    [connection] = smtp.connections
    assert (connection.port, connection.implicit_tls) == (465, True)
    assert [call[0] for call in connection.calls] == ["login", "send", "quit"]


def test_building_it_does_not_connect(smtp):
    """
    Checks: building the notifier opens no connection; it only connects when a failure is notified.

    If it fails: the DAG file, which Airflow parses every 30 seconds, would connect to the SMTP server
    on every parse, and could be blocked by it.
    """
    make_notifier(587)

    assert smtp.connections == []
