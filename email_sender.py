import smtplib, argparse, os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

def send_email_with_attachment(subject, message, attachment_path):
    sender_email = os.environ.get("SDNBM_EMAIL_FROM", "")
    receiver_email = os.environ.get("SDNBM_EMAIL_TO", "")
    smtp_server = os.environ.get("SDNBM_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SDNBM_SMTP_PORT", "587"))  # TLS default
    username = os.environ.get("SDNBM_SMTP_USER", "")
    password = os.environ.get("SDNBM_SMTP_PASS", "")

    if not (sender_email and receiver_email and username and password):
        raise RuntimeError(
            "Configuração de e-mail ausente. Defina as variáveis de ambiente "
            "SDNBM_EMAIL_FROM, SDNBM_EMAIL_TO, SDNBM_SMTP_USER e SDNBM_SMTP_PASS "
            "(opcional: SDNBM_SMTP_HOST, SDNBM_SMTP_PORT)."
        )

    # Create a multipart email message
    email_message = MIMEMultipart()
    email_message['Subject'] = subject
    email_message['From'] = sender_email
    email_message['To'] = receiver_email


    # Attach the message text
    email_message.attach(MIMEText(message, 'plain'))

    for att in attachment_path:
        # Open the file in bynary
        with open(att, 'rb') as attachment_file:
            # Add the file as an attachment
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(attachment_file.read())

        # Encode the attachment
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f"attachment; filename= {att}")

        # Add the attachment to the email
        email_message.attach(attachment)

    # Connect to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Enable encryption (TLS)

    # Login to your email account
    server.login(username, password)

    # Send the email
    server.sendmail(sender_email, receiver_email, email_message.as_string())

    # Disconnect from the server
    server.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to send emails with results from DEI cloud-server.')
        
    parser.add_argument('-s','--subject', help='Subject of the message')
    parser.add_argument('-m','--message', help='Content of the message')
    parser.add_argument('-a','--attach', nargs='+', help='PATH/TO/FILE')

    args = parser.parse_args()

    send_email_with_attachment(args.subject, args.message, args.attach)