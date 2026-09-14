import smtplib
from email.message import EmailMessage
from datetime import datetime


def send_email(receiver, student_name, complaint_id, category):

    msg = EmailMessage()

    msg["Subject"] = "CampusAI - Complaint Resolved"
    msg["From"] = "CampusAI Support <smartcampusai7@gmail.com>"
    msg["To"] = receiver

    msg.set_content(
        "Your email client does not support HTML emails."
    )

    resolved_date = datetime.now().strftime("%d-%b-%Y %I:%M %p")

    msg.add_alternative(f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial,sans-serif;background:#f4f6f9;padding:25px;">

    <div style="
        max-width:650px;
        margin:auto;
        background:white;
        border-radius:12px;
        overflow:hidden;
        box-shadow:0 0 12px rgba(0,0,0,0.15);
    ">

        <div style="
            background:#0d6efd;
            color:white;
            padding:20px;
            text-align:center;
        ">
            <h1 style="margin:0;">🏫 CampusAI</h1>
            <p style="margin-top:8px;">
                AI Based Smart Campus Governance System
            </p>
        </div>

        <div style="padding:30px;">

            <h2>Hello {student_name}, 👋</h2>

            <p style="font-size:16px;">
                ✅ Your complaint has been
                <b style="color:green;">Resolved Successfully</b>.
            </p>

            <table style="
                width:100%;
                border-collapse:collapse;
                margin-top:20px;
            ">

                <tr>
                    <td style="padding:10px;border:1px solid #ddd;"><b>Complaint ID</b></td>
                    <td style="padding:10px;border:1px solid #ddd;">CMP{complaint_id}</td>
                </tr>

                <tr>
                    <td style="padding:10px;border:1px solid #ddd;"><b>Category</b></td>
                    <td style="padding:10px;border:1px solid #ddd;">{category}</td>
                </tr>

                <tr>
                    <td style="padding:10px;border:1px solid #ddd;"><b>Status</b></td>
                    <td style="padding:10px;border:1px solid #ddd;color:green;">
                        Resolved ✅
                    </td>
                </tr>

                <tr>
                    <td style="padding:10px;border:1px solid #ddd;"><b>Resolved On</b></td>
                    <td style="padding:10px;border:1px solid #ddd;">
                        {resolved_date}
                    </td>
                </tr>

            </table>

            <p style="margin-top:25px;">
                Thank you for using <b>CampusAI</b>.
            </p>

            <hr>

            <p style="
                text-align:center;
                color:gray;
                font-size:13px;
            ">
                CampusAI Support Team<br>
                AI Based Smart Campus Governance System
            </p>

        </div>

    </div>

    </body>
    </html>
    """, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(
            "smartcampusai7@gmail.com",
            "mkbt rksw hxmp tglh"
        )

        server.send_message(msg)