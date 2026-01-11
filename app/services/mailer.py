def send_activation_email(email: str, code: str):
    """Mocked SMTP service, to send an activation code to the user's email."""
    print(f"[SMTP] Code d'activation pour {email}: {code}")
