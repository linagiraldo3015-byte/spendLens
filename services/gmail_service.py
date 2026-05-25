import base64
import email as email_lib
from dataclasses import dataclass
from email.header import decode_header
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from config.settings import (
    BANK_SENDERS,
    GMAIL_CREDENTIALS_PATH,
    GMAIL_SCOPES,
    GMAIL_TOKEN_PATH,
)


@dataclass
class EmailMessage:
    message_id: str
    subject: str
    sender: str
    body: str


def authenticate() -> Credentials:
    """Autentica con Gmail OAuth 2.0 y retorna credenciales validas."""
    creds: Optional[Credentials] = None

    if GMAIL_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(
            str(GMAIL_TOKEN_PATH), GMAIL_SCOPES
        )

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not GMAIL_CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"No se encontro {GMAIL_CREDENTIALS_PATH}. "
                "Descarga el archivo credentials.json desde Google Cloud Console "
                "y colocalo en la raiz del proyecto."
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(GMAIL_CREDENTIALS_PATH), GMAIL_SCOPES
        )
        creds = flow.run_local_server(port=0)

    GMAIL_TOKEN_PATH.write_text(creds.to_json())
    return creds


def get_gmail_service() -> Resource:
    """Retorna un cliente autenticado de la Gmail API."""
    creds = authenticate()
    return build("gmail", "v1", credentials=creds)


def build_bank_query(max_days: int = 7) -> str:
    """Construye el query de Gmail para filtrar correos bancarios recientes."""
    sender_filter = " OR ".join(f"from:{s}" for s in BANK_SENDERS)
    return f"is:unread newer_than:{max_days}d ({sender_filter})"


def list_bank_emails(
    max_results: int = 20,
    max_days: int = 7,
) -> list[EmailMessage]:
    """Lista correos no leidos de remitentes bancarios."""
    service = get_gmail_service()
    query = build_bank_query(max_days)

    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    message_ids = response.get("messages", [])
    if not message_ids:
        return []

    emails: list[EmailMessage] = []
    for msg_ref in message_ids:
        msg = fetch_email(service, msg_ref["id"])
        if msg:
            emails.append(msg)

    return emails


def fetch_email(service: Resource, message_id: str) -> Optional[EmailMessage]:
    """Obtiene el contenido completo de un correo por su ID."""
    raw = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    headers = {h["name"].lower(): h["value"] for h in raw["payload"]["headers"]}
    subject = _decode_header_value(headers.get("subject", ""))
    sender = headers.get("from", "")
    body = _extract_body(raw["payload"])

    return EmailMessage(
        message_id=message_id,
        subject=subject,
        sender=sender,
        body=body,
    )


def mark_as_read(service: Resource, message_id: str) -> None:
    """Marca un correo como leido removiendo la etiqueta UNREAD."""
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()


def _extract_body(payload: dict) -> str:
    """Extrae el texto plano del cuerpo de un correo."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode_base64(payload["body"]["data"])

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return _decode_base64(part["body"]["data"])
        if part.get("parts"):
            result = _extract_body(part)
            if result:
                return result

    if payload.get("body", {}).get("data"):
        return _decode_base64(payload["body"]["data"])

    return ""


def _decode_base64(data: str) -> str:
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")


def _decode_header_value(value: str) -> str:
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)
