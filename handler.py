import datetime
import time
import logging
import requests
import json
import os
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LEADERBOARD_ID = os.environ['LEADERBOARD_ID']
LEADERBOARD_SESSION = os.environ['LEADERBOARD_SESSION']
SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
LEADERBOARD_URL = "https://adventofcode.com/{}/leaderboard/private/view/{}".format(
    datetime.datetime.today().year, LEADERBOARD_ID)


def get_leader_board():
    """ Grab the Leaderboard from AoC """
    r = requests.get("{}.json".format(LEADERBOARD_URL),
                     cookies={"session": LEADERBOARD_SESSION})

    if r.status_code != requests.codes.ok:
        print("Error retrieving leaderboard")

    return r.json()


def build_message(new_stars):
    """ Build up the messages to be sent """
    str = ""
    messages = [
        ":star: *{name}* just completed a challenge, they now have *{stars}* stars!\n",
        ":star: Get in! *{name}* just bagged a star. Their total is now *{stars}* stars.\n",
        ":star: DingDing! *{name}* only just went and got a star, that makes *{stars}*.\n",
        ":star: Is it a Bird? Is it a Plane? No, it's *{name}* with *{stars}* stars.\n",
        ":star: BREAKING NEWS: *{name}* is smashing it with {stars} stars.\n"
    ]

    for member in new_stars:
        msg = random.choice(messages)
        str += msg.format(name=member['name'], stars=member['stars'])

    return str


def get_new_stars(leaderboard):
    """ Format the payload of the leaderboard to something more useful, filter to stars only gained since last run """
    last_run = int(time.time()) - 3600
    new_stars = []

    for member in leaderboard.values():
        if int(member['last_star_ts']) > last_run:
            new_stars.append({
                "name": member['name'],
                "stars": member['stars'],
                "last_ts": member['last_star_ts']
            })

    return new_stars


def send_webhook(msg):
    """ Send the slack webhook """
    slack_data = {
        "username": "AoC Starbot",
        "icon_emoji": "robot_face",
        "text": msg
    }

    requests.post(SLACK_WEBHOOK, data=json.dumps(slack_data),
                  headers={'Content-Type': 'application/json'})


def run(event, context):
    """ main """
    print(10*"~" + " AoC StarBot " + 10*"~")

    leaderboard = get_leader_board()
    stars = get_new_stars(leaderboard["members"])
    msg = build_message(stars)

    print(msg)

    if msg != "":
        send_webhook(msg)
