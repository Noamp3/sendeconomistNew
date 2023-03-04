import time
from datetime import datetime, timedelta
import requests
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import yaml
import os

COMMASPACE = ', '
msg_text = ""


def compose_email(from_addr, to_addr, subject, body, file):
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body))

    if file:
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(open(filename, 'rb').read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment',
                              filename=filename)
        msg.attach(attachment)

    return msg


def send_email(msg, from_addr, to_addr, smtp_port, smtp_user, smtp_password):
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(from_email, [to_addr], msg.as_string())
    server.quit()


def download_latest_economist():
    try:
        msg_text = ""
        # Get the latest folder URL in the repository
        repo_url = 'https://github.com/hehonghui/awesome-english-ebooks/tree/master/01_economist'
        response = requests.get(repo_url)
        folder_urls = re.findall(r'href="(.*?)"', response.text)
        latest_folder_url = max(url for url in folder_urls if url.startswith(
            '/hehonghui/awesome-english-ebooks/tree/master/01_economist/'))

        # Get the latest epub file URL in the latest folder
        latest_folder_url = 'https://github.com' + latest_folder_url
        response = requests.get(latest_folder_url)
        file_urls = re.findall(r'href="(.*?)"', response.text)
        latest_epub_file_url = max(
            url for url in file_urls if url.endswith('.epub'))

        # Get the actual download link of the latest epub file
        raw_url = latest_epub_file_url.replace('/blob/', '/raw/')

        # Download the latest epub file
        response = requests.get('https://github.com' + raw_url)
        filename = raw_url.split('/')[-1]
        with open(filename, 'wb') as f:
            f.write(response.content)
        msg_text += f'\nThe file "{filename}" was downloaded successfully.'
        print(msg_text)
        saturday = str(datetime.today().date() + timedelta(days=1)).replace(
            '-', '.')
        if saturday in filename:
            return True, filename
        return False, filename
    except Exception as e:
        msg_text += f'\nAn error occurred while downloading the file: {e}'
        print(msg_text)
        return False, filename



# Load the email configuration from the YAML file
with open('configTest.yml', 'r') as f:
    config = yaml.safe_load(f)['email']
smtp_host = config['smtp_host']
smtp_port = config['smtp_port']
smtp_username = config['smtp_username']
smtp_password = config['smtp_password']
from_email = config['from_email']
to_email = config['to_email']
day_to_run = config['day_to_run']

# run the script only if it's friday
if datetime.today().weekday() == day_to_run:
    count = 0
    while count < 3:
        download_success, filename = download_latest_economist()
        if download_success:
            break
        count += 1
        time.sleep(60*60*3)

    # Compose the email message
    if download_success:
        text = 'Please find the latest Economist ebook attached.'
        try:
            msg = compose_email(from_email, COMMASPACE.join([to_email]),
                                'Latest Economist ebook', text, filename)
        except Exception as e:
            msg_text += f'\nAn error occurred while attaching the file: {e}'
            print(msg_text)
    else:
        msg_text += 'The latest Economist ebook was not found or could not be downloaded.'


    # Send the email using SMTP
    try:
        send_email(msg, from_email, to_email, smtp_port, smtp_username, smtp_password)
        msg_text += f'\nThe email was sent successfully.'
    except Exception as e:
        download_success = False
        msg_text += f'\nAn error occurred while sending the email: {e}'
        print(msg_text)

    # Send an info mail
    status = 'Success!' if download_success else 'Failed!:('
    report_msg = compose_email(from_email, from_email,
                        f'Latest Economist ebook sending report - {status}',
                        msg_text, None)
    try:
        send_email(report_msg, from_email, from_email, smtp_port, smtp_username, smtp_password)
    except Exception as e:
        print(f'An error occurred while sending the info email: {e}')

    # Remove the downloaded file
    try:
        os.remove(filename)
        print(f'The file "{filename}" was removed successfully.')
    except Exception as e:
        print(f'An error occurred while removing the file: {e}')
else:
    print('It is not Friday, so the script will not run.')
