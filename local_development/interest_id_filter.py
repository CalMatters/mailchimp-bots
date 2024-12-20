# Interest Id Filter 
# Mailchimp Bot Code Example
# --------------------------

# Imports:
import json
import os
import requests
from datetime import date
from datetime import timedelta 
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
import pdb


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
	# Attempt to get the campaign that you wish to get info from by setting a relevant timeframe (one that will contain the campaign) 
	campaign = client.campaigns.list(count=5, since_send_time='{}T15:00:00.000Z'.format(last_send), before_send_time="{}T19:00.000Z".format(last_send), fields=["campaigns.id", "campaigns.recipients"])  
except ApiClientError as error:
	print("Error: {}".format(error.text))

try:
	# Attempt to get the campaign that you wish to get make a comparison with by setting a relevant timeframe (one that will contain the campaign) 
	campaign_comparison = client.campaigns.list(count=5, since_send_time='{}T15:00:00.000Z'.format(comp_date), before_send_time="{}T19:00:00.000Z".format(comp_date), fields=["campaigns.id", "campaigns.recipients"])  
except ApiClientError as error:
	print("Error: {}".format(error.text))

# Function to check if campaign is a campaign of interest; if it is, return the the campaign id or the number of recipients 
def get_campaign_data(data, get_id = 0):
	interest = []
	return_data = []
	# For each campaign in campaigns 
	for d in data['campaigns']:
		try:
			# attempt to get the interest ids 
			interest = d['recipients']['segment_opts']['conditions'][0]['value']
		except KeyError as ke:
			pass
		if (os.environ['INTEREST_ID'] in interest):
			# If this is the correct campaign and get_id is set, return the campaign id,
            # otherwise return the recipient count
			return_data = d['id'] if get_id else d['recipients']['recipient_count']
			break
	# Return the relvant data
	return return_data 

campaign_id = get_campaign_data(campaign, 1)

# pdb.set_trace()
# If campaign_id is empty, exit the program
if not campaign_id:
	requests.post(os.environ['SLACK_WEBHOOK'], headers=headers, data='{"text": "*Note*: No WeeklyMatters campaign found for ' + last_send.strftime('%b %d, %Y') + '." }')

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
	# Attempt to get a campaign report
	campaign_report = client.reports.get_campaign_report(campaign_id, fields = report_fields)
except ApiClientError as error:
	print("Error: {}".format(error.text))

# Set the rest of the metrics starting with the number of recipients "
list_size = get_campaign_data(campaign) 
previous_list_size = get_campaign_data(campaign_comparison)
# pdb.set_trace()
# If the previous list size existes, continue. 
if previous_list_size:
	list_numerical_diff = list_size - previous_list_size
	list_diff = round((list_numerical_diff)/list_size*100, 1)
	if list_numerical_diff > 0:
		list_note = '*+{:,}* subscribers (+{}%)'.format(list_numerical_diff, list_diff)
	else:
		list_note = '*{:,}* subscribers ({}%)'.format(list_numerical_diff, list_diff)
else: # otherwise, exit
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
				"text": "WeeklyMatters | {}".format(last_send.strftime('%A, %B %d, %Y')),
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
# pdb.set_trace()
requests.post(os.environ['SLACK_WEBHOOK'], headers=headers, data=blocks.encode('utf-8'))