# yewcal

Yewcal is a command line event planner/calendar. 

## Features

* Add, edit, delete calendar entries

* Show calendar entries

* Notifications of impending events, email, sms, Slack

* Day's upcoming events in email

* Selectively pull Google Calendar events

* Syncronise to notification server

You can run a cron job to send notifications about imminent
events. You can push the event data to an AWS bucket to access from
some server and easily pull it and notify.

## Usage

Create a new event:

``` shell
yc create "Karl's birthday" "in 3 days"
```

Show today's events
``` shell
❯ yc today
Thu 2020-12-03      3996d419  12:30   Karl lecture: https:  CET            1:00:00
                    b1871798  15:09   Peter's birthday      CET            1:00:00
                    b358a46d  16:00   Weekly Management Ca  Europe/London  1:00:00
```

Edit an event by providing the id. 

``` shell
yc edit 3996d419
```

Show tomorrow's events

``` shell
yc tomorrow
```

``` shell
❯ yc
Usage: yc.py [OPTIONS] COMMAND [ARGS]...

Options:
  --user TEXT  User name
  -d, --debug  Debug flag
  --help       Show this message and exit.

Commands:
  all                 List all events, past and future.
  cal                 Show calendar for months.
  check               Show how a data string will be interpreted.
  create              Create a calendar event.
  describe            Show detail about a calendar event.
  edit                Edit a calendar event.
  future              Show all future events.
  info                Show information about settings.
  notify-soon         Process notifications for imminent events.
  notify-today        Show today's events.
  pull-events         Pull event data from remote storage.
  pull-google-events  Interactively pull data from user's google calendar.
  push-events         Push event data to remote storage.
  today               Show today's events.
  tomorrow            Show tomorrow's events.
  tz                  List all timezones.
```

## Date specification

We use the [dateparser](https://github.com/scrapinghub/dateparser)
package to parse dates. There is a command "check" that can be used to
check the result of a natural language date:

``` shell
❯ yc check "in a week"
2020-12-10T09:07:51.727824
❯ yc check "in 4 days"
2020-12-07T09:08:32.258311
❯ yc check "in 4 weeks"
2020-12-31T09:08:38.632423
❯ yc check tomorrow
2020-12-04T09:09:13.509811
❯ yc check today
2020-12-03T09:09:18.396979
❯ yc check "in two months"
2021-02-03T09:12:58.198817
❯ yc check "12 december"
2020-12-12T00:00:00
❯ yc check "12 dec"
2020-12-12T00:00:00
```

## Timezones

Yewcal will detect and use the local timezone as the default
timezone. But you can specify different timezones for each
event. Timezones can be specified with `-t`:

``` shell
yc create "Management meeting" thursday -t london
```

## cron jobs

The reason for the system of setting up an AWS bucket is to give
access to a server side instance of yewcal to enable notifications
even when your workstation is not running or you want notifications on
your phone.

Here are three crons for the server:

``` shell
# pull data locally 
*/15 * * * * cd /home/someuser/yewcal && /home/someuser/yewcal/.venv/bin/python3.8 yc.py pull-events >>  /home/someuser/yewcal/cron.log 2>&1

# send notifications for events that are happening in the next few minutes
*/5 * * * * cd /home/someuser/yewcal && /home/someuser/yewcal/.venv/bin/python3.8 yc.py notify-soon >>  /home/someuser/yewcal/cron.log 2>&1

# send an email at 8am every morning with a digest of events for the day
0 8 * * * cd /home/someuser/yewcal && /home/paul/yewcal/.venv/bin/python3.8 yc.py notify-today >>  /home/someuser/yewcal/cron.log 2>&1
```

You would either need to manually push your event data to the AWS bucket or setup a cron on your local machine to regularly update the remote copy of data. 

##  Google Calendar

There is an integration with Google calendar. You need to setup your credentials. Check for where your data directory is:

``` shell
❯ yc info
constants.BASE_DATA_PATH='/Users/paul/.yew.d/paul/cal'
constants.EVENTS_FILENAME='events.json'
constants.CURRENT_TZ=datetime.timezone(datetime.timedelta(seconds=3600), 'CET')
constants.DEFAULT_TZ_NAME='CET'
```

Put these files in the BASE_DATA_PATH:

* credentials.json
* token.pickle

Instructions for creating these are here <https://developers.google.com/calendar/quickstart/python>.

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

