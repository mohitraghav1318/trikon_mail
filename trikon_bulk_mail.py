"""
Trikon 3.0 - Bulk Email Sender with QR Code Attachment
=======================================================
Setup:
  1. pip install secure-smtplib
  2. Gmail mein App Password banao:
     Gmail → Settings → Security → 2-Step Verification → App Passwords
  3. Apni details neeche fill karo (CONFIGURE HERE section)
  4. python trikon_bulk_mail.py

CSV format (data.csv):
  name,email,team,qr_file
  Aarav Sharma,aarav@gmail.com,Team Alpha,TRK-001.png
  Priya Nair,priya@gmail.com,Team Beta,TRK-002.png
"""

import smtplib
import csv
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# ─────────────────────────────────────────────
#  CONFIGURE HERE — sirf yahan changes karo
# ─────────────────────────────────────────────

GMAIL_ADDRESS  = "intelliasociety@gmail.com"   # apna Gmail
GMAIL_APP_PASS = "fcxtjqutkfppkugv"       # 16-digit App Password (spaces theek hain)

CSV_FILE       = "data.csv"                   # CSV file ka naam
QR_FOLDER      = "qr_codes"                   # folder jahan QR images hain

SENDER_NAME    = "Trikon 3.0 Team"
SUBJECT        = "Congratulations! You're Qualified for Trikon 3.0 🎉"

# ─────────────────────────────────────────────
#  EMAIL TEMPLATE  — {{name}}, {{team}} use karo
# ─────────────────────────────────────────────

EMAIL_BODY = """\
Dear {{name}},

We are thrilled to inform you that you have been officially selected and 
QUALIFIED for Trikon 3.0! 🎉

Your team "{{team}}" has made it through the selection process.

Please find your personal QR code attached to this email.
You will need to present this QR code at the event venue for entry.

━━━━━━━━━━━━━━━━━━━━━━━
  Event   : Trikon 3.0
  Team    : {{team}}
  Name    : {{name}}
━━━━━━━━━━━━━━━━━━━━━━━

Important:
  • Keep this QR code safe — it is unique to you
  • Carry this email or a screenshot of the QR on event day
  • Do not share your QR code with anyone

We look forward to seeing you at the event!

Warm regards,
Trikon 3.0 Team
"""

# ─────────────────────────────────────────────
#  SCRIPT — kuch change karne ki zaroorat nahi
# ─────────────────────────────────────────────

def fill_template(text, name, team):
    return text.replace("{{name}}", name).replace("{{team}}", team)


def send_email(smtp, row, sender_email, sender_name):
    name     = row.get("name", "").strip()
    email    = row.get("email", "").strip()
    team     = row.get("team", "").strip()
    qr_file  = row.get("qr_file", "").strip()

    if not email or "@" not in email:
        return False, "Invalid email"

    # Try direct path first, then look inside team subfolder
    qr_path = None
    if qr_file:
        direct = os.path.join(QR_FOLDER, qr_file)
        in_team = os.path.join(QR_FOLDER, team, qr_file)
        if os.path.exists(direct):
            qr_path = direct
        elif os.path.exists(in_team):
            qr_path = in_team
        else:
            return False, f"QR file not found: {qr_file} (tried direct + {team}/)"

    msg = MIMEMultipart()
    msg["From"]    = f"{sender_name} <{sender_email}>"
    msg["To"]      = email
    msg["Subject"] = fill_template(SUBJECT, name, team)

    body = fill_template(EMAIL_BODY, name, team)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if qr_path:
        with open(qr_path, "rb") as f:
            img = MIMEImage(f.read(), name=os.path.basename(qr_path))
            img.add_header("Content-Disposition", "attachment",
                           filename=f"QR_{name.replace(' ', '_')}.png")
            msg.attach(img)

    smtp.sendmail(sender_email, email, msg.as_string())
    return True, "Sent"


def main():
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV file '{CSV_FILE}' nahi mili!")
        print("   Ek CSV banao is format mein:")
        print("   name,email,team,qr_file")
        print("   Aarav Sharma,aarav@gmail.com,Team Alpha,TRK-001.png")
        return

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total   = len(rows)
    sent    = 0
    failed  = 0
    skipped = 0

    print(f"\n{'─'*50}")
    print(f"  Trikon 3.0 — Bulk Email Sender")
    print(f"{'─'*50}")
    print(f"  Total recipients : {total}")
    print(f"  Gmail account    : {GMAIL_ADDRESS}")
    print(f"  QR folder        : {QR_FOLDER}/")
    print(f"{'─'*50}\n")

    confirm = input(f"Kya aap {total} emails bhejna chahte ho? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y", "haan", "ha"):
        print("Cancelled.")
        return

    print("\nConnecting to Gmail...\n")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            print("✅ Gmail se connect ho gaye!\n")

            for i, row in enumerate(rows, 1):
                name  = row.get("name", f"Person {i}").strip()
                email = row.get("email", "").strip()

                print(f"[{i:03d}/{total}] {name} <{email}>", end=" ... ")

                try:
                    ok, msg = send_email(smtp, row, GMAIL_ADDRESS, SENDER_NAME)
                    if ok:
                        print(f"✅ {msg}")
                        sent += 1
                    else:
                        print(f"⚠️  Skipped — {msg}")
                        skipped += 1
                except Exception as e:
                    print(f"❌ Failed — {e}")
                    failed += 1

                # Gmail rate limit se bachne ke liye thoda wait
                time.sleep(1.2)

    except smtplib.SMTPAuthenticationError:
        print("\n❌ Authentication failed!")
        print("   Check karo:")
        print("   1. App Password sahi hai?")
        print("   2. Gmail mein 2-Step Verification on hai?")
        print("   3. Gmail address sahi hai?")
        return
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        return

    print(f"\n{'─'*50}")
    print(f"  Done!")
    print(f"  Sent    : {sent}")
    print(f"  Skipped : {skipped}")
    print(f"  Failed  : {failed}")
    print(f"{'─'*50}\n")


if __name__ == "__main__":
    main()