import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from getpass import getpass

sender_email = input('Your email: ')
password = getpass('Your email password: ')
receiver_email = input('Recipient email: ')

files_dir = os.path.dirname(os.path.abspath(__file__)) + '/files'

filename = input('File name: ')

if filename.find('../') != -1:
    print('!!! Injection attempt, exiting !!!')
    exit(-2)
if not filename.endswith('.html') and not filename.endswith('.txt'):
    print('Unsupported file format')
    exit(-1)

with open(f'{files_dir}/{filename}', 'r') as file:
    subject = filename
    body = file.read()

msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))

try:
    server = smtplib.SMTP()
    server.connect('smtp.mail.ru', 465)
    server.login(sender_email, password)
    
    server.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")
finally:
    server.quit()
