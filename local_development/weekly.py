# Weekly Mailchimp Bot Code
# --------------------------

# Imports:
import json
import os
import requests
from datetime import date
from datetime import timedelta 
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
# import re
# import pdb


## Set up the Mailchimp Client by providing the Mailchimp Key and server
client = MailchimpMarketing.Client()
client.set_config({
	"api_key": os.environ['MAILCHIMP_KEY'],
	"server": os.environ['MAILCHIMP_SERVER']
	})

# Set the date for the campaign you wish to get. 
last_send = date.today() - timedelta(days = 3)

# Get Comp Time 
comp_date = last_send - timedelta(days = 7)

# Set the headers for the post to Slack
headers = {
	'Content-type': 'application/json',
}

try:
	# Attempt to get the campaign that you wish to get info from by setting a relevant timeframe and providing the relevant folder id 
	campaign = client.campaigns.list(count=5, since_send_time='{}T11:00:00.000Z'.format(last_send), before_send_time="{}T22:00.000Z".format(last_send), folder_id=os.environ['FOLDER_ID'], fields=["campaigns.id", "campaigns.recipients"])  
except ApiClientError as error:
	print("Error: {}".format(error.text))

# pdb.set_trace()
try:
	# Attempt to get the campaign that you wish to get make a comparison with by setting a relevant timeframe and providing the relevant folder id 
	campaign_comparison = client.campaigns.list(count=5, since_send_time='{}T11:00:00.000Z'.format(comp_date), before_send_time="{}T22:00:00.000Z".format(comp_date), folder_id=os.environ['FOLDER_ID'], fields=["campaigns.id", "campaigns.recipients"])  
except ApiClientError as error:
	print("Error: {}".format(error.text))

# pdb.set_trace()
try:
	# If the campaign was found, set the id here. 
	campaign_id = campaign['campaigns'][0]['id']
except IndexError as error:
	# Otherwise post in Slack that the bot was unable to find a campaign and record the error in the console
	requests.post(os.environ['SLACK_WEBHOOK'], headers=headers, data='{"text": "*Note*: No yourCampaignNameHere campaign found for ' + last_send.strftime('%b %d, %Y') + '." }')
	
# -- Get other relevant reports from the mailchimp API

# Set the fields you wish to get from the MailChimp Reports API request
report_fields = [
	"id",
	'campaign_title',
	'subject_line',
	'emails_sent',
	'unsubscribed',
	'bounces',
	'opens',
	'clicks',
]

try:
	# Attempt to get the other two reports: a campaign report and a click report 
	campaign_report = client.reports.get_campaign_report(campaign_id, fields = report_fields)
except ApiClientError as error:
	print("Error: {}".format(error.text))

# Set the rest of the metrics metrics
list_size = campaign['campaigns'][0]['recipients']['recipient_count'] 
try: 
	previous_list_size = campaign_comparison['campaigns'][0]['recipients']['recipient_count'] 
	list_numerical_diff = list_size - previous_list_size
	list_diff = round((list_numerical_diff)/list_size*100, 1)
	if list_numerical_diff > 0:
		list_note = '*+{:,}* subscribers (+{}%)'.format(list_numerical_diff, list_diff)
	else:
		list_note = '*{:,}* subscribers ({}%)'.format(list_numerical_diff, list_diff)
except IndexError as error:
	list_note = '_Comparison not available_'
	
subject_line = campaign_report['subject_line']
open_rate = round(campaign_report['opens']['open_rate']*100, 1)
ctor = round(campaign_report['clicks']['unique_subscriber_clicks']/campaign_report['opens']['unique_opens']*100, 1)
unsubs = campaign_report['unsubscribed']
unsub_rate = round(unsubs / list_size * 100, 2)
bounces = campaign_report['bounces']['hard_bounces'] + campaign_report['bounces']['soft_bounces']
bounce_rate = round(bounces / list_size * 100, 2)  
deliverability = 100 - bounce_rate
opens = campaign_report['opens']['unique_opens']


# Fill in the content using the Slack Block 
set_blocks = {
	"blocks": [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "yourCampaignNameHere | {}".format(last_send.strftime('%A, %B %d, %Y')),
				"emoji": True
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*{}*".format(subject_line)
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": " - Open Rate: *{}%* ({:,} unique opens) \n - Click to Open Rate: *{}%*".format( open_rate, opens, ctor)
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Other Notes: \n - List Size: *{:,}* \n - Net Change: {} \n - Delivery Rate: *{}%* ({:,} bounces) \n - Unsubscribes: *{:,}* ({}% of the list)".format(list_size, list_note, deliverability, bounces, unsubs, unsub_rate)
			}
		}
	]
}

blocks = json.dumps(set_blocks)
# print(blocks)
requests.post(os.environ['SLACK_WEBHOOK'], headers=headers, data=blocks.encode('utf-8'))
