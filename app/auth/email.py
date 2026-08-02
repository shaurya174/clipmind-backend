from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}


def _env_int(name: str, default: int) -> int:
	value = os.getenv(name)

	if value is None or not value.strip():
		return default

	return int(value)


SMTP_PORT = _env_int("SMTP_PORT", 587)
SMTP_TIMEOUT_SECONDS = _env_int("SMTP_TIMEOUT_SECONDS", 15)


def email_delivery_enabled() -> bool:
	return bool(SMTP_HOST and SMTP_FROM_EMAIL)


def send_email(to_email: str, subject: str, body: str) -> bool:
	"""
	Send a plain-text email when SMTP settings are configured.

	Returns True when delivery was attempted successfully. Returns False when
	SMTP is not configured, so local development can continue without mail.
	"""

	if not email_delivery_enabled():
		return False

	message = EmailMessage()
	message["From"] = SMTP_FROM_EMAIL
	message["To"] = to_email
	message["Subject"] = subject
	message.set_content(body)

	if SMTP_USE_SSL:
		context = ssl.create_default_context()
		with smtplib.SMTP_SSL(
			SMTP_HOST,
			SMTP_PORT,
			timeout=SMTP_TIMEOUT_SECONDS,
			context=context,
		) as smtp:
			if SMTP_USERNAME and SMTP_PASSWORD:
				smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
			smtp.send_message(message)
		return True

	with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
		if SMTP_USE_TLS:
			smtp.starttls(context=ssl.create_default_context())

		if SMTP_USERNAME and SMTP_PASSWORD:
			smtp.login(SMTP_USERNAME, SMTP_PASSWORD)

		smtp.send_message(message)

	return True
