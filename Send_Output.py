import logging
import boto3
import botocore.client
import os
import datetime
import time
import smtplib
import email.mime.text
import email.utils


## Check S3 bucket for today's output file and send out via email. 
## If today's file isn't uploaded, wait 10 minutes and retry.

attempt=0
def send_output(attempt):               
    if attempt > 3:
        print("Too Many Attempts")
        return
    s3 = boto3.client('s3')
    objects = s3.list_objects_v2(Bucket='osrs-grand-exchange-final-list')
    last_modified = objects["Contents"][0]["LastModified"]
    lm_split = str(last_modified).split()
    current_date = datetime.date.today()

    if str(current_date) == lm_split[0]:
        with open('/home/ec2-user/PROJECTFOLDER/final_list.csv', 'wb') as f:
            s3.download_fileobj('osrs-grand-exchange-final-list', 'final_list_csv', f)
      
        with open('/home/ec2-user/PROJECTFOLDER/final_list.csv') as fp:
            msg = email.mime.text.MIMEText(fp.read())


        msg['To'] = email.utils.formataddr(('Recipient', 'recipient@email.com'))
        msg['From'] = email.utils.formataddr(('Sender', 'sender@email.com'))
        msg['Subject'] = "Today's Final List"

        server = smtplib.SMTP_SSL('smtp.gmail.com')
        server.connect('smtp.gmail.com', 465)

 


        ## TO SEND MAIL FROM EC2 INSTANCE YOU MUST SET UP AN APP PASSWORD LOGIN FROM THE SENDER'S MAIL
        server.login('sender@email.com', 
        'YOUR APP PASSWORD FOR SENDER@EMAIL.COM')


        try:
            server.sendmail('sender@email.com', ['OSRSPROJECTTEST@yahoo.com'], msg.as_string())
            print("Success")
        except:
            print("Failed")
        finally:
            server.close()

    else:
        time.sleep(600)
        send_output(attempt+1)

send_output(attempt)