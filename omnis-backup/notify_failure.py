"""
E-mails that a backup failed, with its error log: notify_failure.py <what was copied> <copy folder> <error log>.
Sent to ALERT_EMAIL through SMTP_HOST as SMTP_USER, who is also the sender, the same way as the engine's
EmailNotifier (which can't be imported here: the omnis package needs Airflow). Port 465 uses implicit
TLS; any other port, STARTTLS (SMTP_PORT defaults to 587). Without ALERT_EMAIL, SMTP_HOST, SMTP_USER
and SMTP_PASSWORD it only says so.
"""
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

what, folder, log = sys.argv[1:]
to, host, user, password = (os.environ.get(name) for name in ("ALERT_EMAIL", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))
if not (to and host and user and password):
    print("The failure is not e-mailed: ALERT_EMAIL, SMTP_HOST, SMTP_USER and SMTP_PASSWORD must all be set")
    sys.exit(0)
port = int(os.environ.get("SMTP_PORT") or 587)

with open(log, encoding="utf-8", errors="replace") as file:
    error = file.read().strip()

message = EmailMessage()
message["From"] = user
message["To"] = to
message["Subject"] = f"Omnis: the backup of {what} failed"
message.set_content(
    f"The monthly backup of {what} failed, and it won't be retried this month. What it copied is in {folder}."
    f"\nOnce it is fixed, delete that folder and the backup will run again within the hour."
    f"\n\nError:\n{error}"
)

context = ssl.create_default_context()
if port == 465:
    with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(message)
else:
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls(context=context)
        smtp.login(user, password)
        smtp.send_message(message)
print(f"Failure e-mailed to {to}")
