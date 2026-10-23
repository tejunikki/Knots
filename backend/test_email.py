from dotenv import load_dotenv
load_dotenv()

from notifications.email import send_resend

to_email = input("Enter your own Gmail address: ").strip()

result = send_resend(
    to_email,
    "AI Release Radar - Test Email",
    "<h2>Email test successful!</h2><p>Resend connection test.</p>"
)

print("Email status:", result)