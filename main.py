from openai import OpenAI
from dotenv import load_dotenv
import os
import csv
import json
import base64
import re

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()
client = OpenAI()

# Gmail API scope
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Output file
CSV_FILE = "gmail_sorted_emails_clean.csv"


# ---------------- LOGIN ----------------
def gmail_login():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ---------------- HELPERS ----------------
def get_header(headers, name):
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def get_email_body(payload):
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="ignore"
                    )

    data = payload["body"].get("data")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return ""


def clean_email_text(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\{.*?\}", " ", text)
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9.,!? ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:800]


# ---------------- AI ----------------
def summarize_email(email_text):
    prompt = f"""
Summarize this email in ONE short sentence.
Max 20 words.

Email:
{email_text}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text.strip()


def classify_email(sender, subject, email_text):
    prompt = f"""
Classify this email into ONE category only:
urgent, important, complaint, congratulation.

Return ONLY valid JSON.

Example:
{{
  "category": "important",
  "remark": "Needs attention but not urgent"
}}

Sender: {sender}
Subject: {subject}
Email text: {email_text}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    ai_text = response.output_text.strip()

    try:
        return json.loads(ai_text)
    except:
        return {
            "category": "important",
            "remark": ai_text[:100]
        }


# ---------------- SAVE ----------------
def save_to_csv(sender, subject, summary, category, remark):
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(
                ["Sender", "Subject", "Summary", "Category", "Remark"]
            )

        writer.writerow([
            sender,
            subject[:100],
            summary[:200],
            category,
            remark[:200]
        ])


# ---------------- MAIN ----------------
def main():
    service = gmail_login()

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="is:unread",
        maxResults=10
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        print("No unread emails found.")
        return

    for msg in messages:
        email = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        payload = email["payload"]
        headers = payload["headers"]

        sender = get_header(headers, "From")
        subject = get_header(headers, "Subject")

        body = get_email_body(payload)

        if body.strip() == "":
            body = email.get("snippet", "")

        body = clean_email_text(body)

        summary = summarize_email(body)
        result = classify_email(sender, subject, body)

        category = result["category"]
        remark = result["remark"]

        save_to_csv(sender, subject, summary, category, remark)

        print("Email saved:")
        print("From:", sender)
        print("Subject:", subject)
        print("Summary:", summary)
        print("Category:", category)
        print("Remark:", remark)
        print("-" * 40)


# Run program
main()