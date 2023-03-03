from datetime import datetime

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


# Load the email configuration from the YAML file
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)['email']
smtp_host = config['smtp_host']
smtp_port = config['smtp_port']
smtp_username = config['smtp_username']
smtp_password = config['smtp_password']
from_email = config['from_email']
to_email = config['to_email']

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
latest_epub_file_url = max(url for url in file_urls if url.endswith('.epub'))

# Get the actual download link of the latest epub file
raw_url = latest_epub_file_url.replace('/blob/', '/raw/')

# run the script only if it's friday
if datetime.today().weekday() == 2:
    # Download the latest epub file
    try:
        response = requests.get('https://github.com' + raw_url)
        filename = raw_url.split('/')[-1]
        with open(filename, 'wb') as f:
            f.write(response.content)
        msg_text = f'The file "{filename}" was downloaded successfully.'
        print(msg_text)
        download_success = True
    except Exception as e:
        msg = f'An error occurred while downloading the file: {e}'
        print(msg_text)
        download_success = False

    # Compose the email message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = COMMASPACE.join([to_email])
    msg['Subject'] = 'Latest Economist ebook'
    if download_success:
        msg.attach(MIMEText('Please find the latest Economist ebook attached.'))
    else:
        msg.attach(MIMEText(msg_text))

    # Attach the file to the email
    if download_success:
        try:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(open(filename, 'rb').read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', 'attachment',
                                  filename=filename)
            msg.attach(attachment)
        except Exception as e:
            msg_text = f'An error occurred while attaching the file: {e}'
            print(msg_text)
            msg.attach(MIMEText(msg))

    # Send the email using SMTP
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        print('The email was sent successfully.')
    except Exception as e:
        print(f'An error occurred while sending the email: {e}')

    # Remove the downloaded file
    try:
        os.remove(filename)
        print(f'The file "{filename}" was removed successfully.')
    except Exception as e:
        print(f'An error occurred while removing the file: {e}')
else:
    print('It is not Friday, so the script will not run.')
