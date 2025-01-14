## Context
The Daily Bot was created to report on a daily newsletter. Run Tuesday through Saturday, it sent metrics to Slack ~24 hours after the campaign was sent. 

## Notes
- The bot provides a comparison between the selected campaign and the previous one. Since the newsletter was only sent on weekdays, if the selected campaign was sent on a Monday, the Friday campaign was used as the comparison. 
- Since this bot uses a folder ID to filter the campaigns, and only one newsletter was sent per day, the time range was expansive.
- While the top clicked links are highlighted in the Slack message, they were also filtered to exclude links that recieved copious amounts of bot traffic. 

![Daily Bot](/data_samples/redacted_daily.png)