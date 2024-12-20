from dataclasses import fields
import json
import os
# from datetime import date
# from datetime import timedelta 
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError


# Create a functions to save our results 
def print_json(title, data): 
	with open(title, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=4)

# Configure the Mailchimp CLient
client = MailchimpMarketing.Client()
client.set_config({
	"api_key": os.environ['MAILCHIMP_KEY'],
	"server": os.environ['MAILCHIMP_SERVER']
	})

# Get Folder Ids
# ---------------
# Returns the folowing:
# folders: An array of objects representing campaign folders.
#  - name: The name of the folder.
#  - id: A string that uniquely identifies this campaign folder.
#  - count: The number of campaigns in the folder.
#  total_items: The total number of folders regardless of pagination.
# Reference: https://mailchimp.com/developer/marketing/api/campaign-folders/list-campaign-folders/)
folder_ids = client.campaignFolders.list( count = 50, exclude_fields=["_links", 'folders._links'] )
print_json("data_samples/folders.json", folder_ids)


# Get Audience List
# ---------------
# Returns Audience lists
# Reference: https://mailchimp.com/developer/marketing/api/campaigns/list-campaigns/
audience_lists = client.lists.get_all_lists( fields=["lists.id", "lists.name", "lists.permission_reminder", "lists.campaign_defaults", "lists.stats", "total_items"])
print_json("data_samples/audience_lists.json", audience_lists)


# Get Campaign Ids
# ---------------
# Returns the 10 most recent campaigns
# Reference: https://mailchimp.com/developer/marketing/api/campaigns/list-campaigns/
campaign_list = client.campaigns.list()
print_json("data_samples/recent_campaigns.json", campaign_list)

if 'FOLDER_ID' in os.environ:
	include_fields = ["campaigns.id", "campaigns.email_sent", "campaigns.send_time", 
	"campaigns.recipients.list_id", "campaigns.recipients.segment_opts",
	"campaigns.settings", "campaigns.report_summary", "total_items"
	 ]
	campaign_list = client.campaigns.list( folder_id=os.environ['FOLDER_ID'], fields=include_fields)
	print_json("data_samples/campaigns_in_folder.json", campaign_list)
else:
	print("A folder ID was not set, so campaign data was not requested from the API.")
	


# INTEREST CATEGORIES 
if 'LIST_ID' in os.environ:
	interest_cat = client.lists.get_list_interest_categories(os.environ['LIST_ID'], count = 200, fields=["categories.id", "categories.title", "total_items"]) 
	print_json("data_samples/interest_categories.json", interest_cat)
	
	if 'INTEREST_CAT_ID' in os.environ:
		# INTERESTS in categories
		interests = client.lists.list_interest_category_interests(os.environ['LIST_ID'], os.environ['INTEREST_CAT_ID'], exclude_fields=['_links'])
		print_json("data_samples/interests.json", interests)
	else:
		print("An interest category id was not set, so interest data was not requested from the API.")
else:
	print("A list ID was not set, so interest category data was not requested from the API.")


	