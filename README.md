# yewcal

Yewcal is a command line event planner/calendar. 

## Features

* Add, edit, delete calendar entries

* Show calendar entries

* Notifications of impending events

* Day's upcoming envents in email

* Pull Google Calendar events

* Syncronise to notification server

You can run a cron job to 

## cron jobs

The reason for the system of setting up an AWS bucket is to give
access to a server side instance of yewcal to enable notifications
even when your workstation is not running or you want notifications on
your phone.

Here are three crons for the server:

``` shell
# pull data locally 
*/15 * * * * cd /home/paul/yewcal && /home/someuser/yewcal/.venv/bin/python3.8 yc.py pull-events >>  /home/someuser/yewcal/cron.log 2>&1

# send notifications for events that are happening in the next few minutes
*/5 * * * * cd /home/paul/yewcal && /home/someuser/yewcal/.venv/bin/python3.8 yc.py notify-soon >>  /home/someuser/yewcal/cron.log 2>&1

# send an email at 8am every morning with a digest of events for the day
0 8 * * * cd /home/paul/yewcal && /home/paul/yewcal/.venv/bin/python3.8 yc.py notify-today >>  /home/someuser/yewcal/cron.log 2>&1
```

You would either need to manually push your event data to the AWS bucket or setup a cron on your local machine to regularly update the remote copy of data. 

##  Gooble Calendar

## Settings

In a file called `.env`, have the following settings: 

Personal information:

* MY_EMAIL_ADDRESS: your email address to which notifications are sent
* MY_MOBILE: your mobile number to which notifications are sent

AWS credentials and bucket:

* AWS_ACCESS_KEY_ID: you AWS key id
* AWS_SECRET_ACCESS_KEY: AWS secret key
* BUCKET: the S3 bucket name

Mailgun API credentials:

* MG_API_KEY: Mailgun api key
* MG_API_URL: Mailgun api endpoint
* MG_FROM: a "from" address 

Slack credentials:

* SLACK_TOKEN: Slack api token
* SLACK_API_URL: Slack api endpoint


Twilio settings if using SMS notifications via Twilio:

* TWILIO_ACCOUNT_SID
* TWILIO_AUTH_TOKEN
* TWILIO_ORIGIN_NUMBER




## Syncronising for Notifications

You can install the software on a server and setup a cron job to trigger notifications. 

From your client:

```shell
yc push-events
```

This will store the event data in an AWS bucket. 







Alternatives:

https://calcurse.org/

https://github.com/pimutils/khal

https://github.com/insanum/gcalcli

