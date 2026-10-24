import smtplib
import ssl
from email.message import EmailMessage

from omnis.ports import Notifier


class EmailNotifier(Notifier):
    """
    Notifier by e-mail, sent to `to` through an SMTP server as `user`, who is also the sender.
    Port 465 uses implicit TLS; any other port, STARTTLS (587 is the usual one).
    """

    def __init__(self, host: str, port: int, user: str, password: str, to: str):
        # Nothing connects until a failure is notified: DAG files build their adapters every time they are parsed
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._to = to

    def notify_failure(self, flow: str, run_id: str, reason: str, last_task: str | None) -> None:
        message = EmailMessage()
        message["From"] = self._user
        message["To"] = self._to
        message["Subject"] = f"Omnis: the {flow} flow failed"
        message.set_content(
            f"Run {run_id} of the {flow} flow failed ({reason})."
            + (f"\nThe last task to finish was {last_task}." if last_task else "")
            + "\n\nCheck it in Airflow."
        )
        self._send(message)

    def _send(self, message: EmailMessage) -> None:
        context = ssl.create_default_context()
        if self._port == 465:
            with smtplib.SMTP_SSL(self._host, self._port, context=context, timeout=30) as smtp:
                smtp.login(self._user, self._password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(self._host, self._port, timeout=30) as smtp:
                smtp.starttls(context=context)
                smtp.login(self._user, self._password)
                smtp.send_message(message)
