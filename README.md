# AoC Private Leaderboard Slackbot 
 A quick and dirty slack webhook bot that announces when members of a private leaderboard achieve a star!

## Requirements 
1. [Serverless Framework](https://www.serverless.com/)

## Config
The script utilises `.env` files for config, rename `.env.example` to `.env` and populate, to add a production stage copy the `.env` file to `.env.production`.

`LEADERBOARD_ID` Your private leaderboard ID, this can be found on the AoC Leaderboard Page.

`LEADERBOARD_SESSION` This is your Session token from the AOC website, see the AoC documentation.

`SLACK_WEBHOOK` The slack webhook URL to post to

To set up team members copy `team_members_example.py` to `team_members.py`

## Deploy
Assuming you have your AWS credentials configured correctly run: 
```
serverless deploy --stage={dev|prod}
```

## Local Testing
You can invoke the function locally by running: 
```
serverless invoke local
```

## Quirks
By default the function runs hourly and it currently doesn't check it's last run time so it naively deducts an hour from the current timestamp to filter out which stars to notify about. 

My private leaderboard is using the STARS ordering method, therefore we don't really care about points, this bot reflects that. 
