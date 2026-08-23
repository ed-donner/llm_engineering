import os
import smtplib
from dotenv import load_dotenv

load_dotenv(override=True)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("MY_EMAIL")
SMTP_PASS = os.getenv("PASSWORD")


def send_confirmation_email(patient_email: str, patient_name: str,
                            doctor_name: str, day_of_week: str, time: str, reason: str):
    print(f"EMAIL TOOL CALLED: Sending confirmation to {patient_email}", flush=True)

    subject = "Your Appointment Confirmation"
    body = (
        f"Dear {patient_name},\n\n"
        f"Your appointment has been confirmed:\n"
        f"Doctor: {doctor_name}\n"
        f"Day: {day_of_week}\n"
        f"Time: {time}\n"
        f"Reason: {reason}\n\n"
        f"Please arrive 10 minutes early.\n\n"
        f"Best regards,\nClinic Team"
    )
    
    try:
        with smtplib.SMTP(SMTP_SERVER, 587) as connection:
            connection.starttls()
            connection.login(SMTP_USER, SMTP_PASS)
            connection.sendmail(from_addr=SMTP_USER,to_addrs=patient_email, msg=f"Subject: {subject} \n\n {body}")
        return f"Confirmation email sent to {patient_email}"
    except Exception as e:
        return f"Failed to send email: {e}"

        
        
    