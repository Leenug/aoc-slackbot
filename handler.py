import datetime
import time
import logging
import requests
import json
import os
import random

try:
    from team_members import TEAM_MEMBERS
except ImportError:
    TEAM_MEMBERS = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LEADERBOARD_ID = os.environ['LEADERBOARD_ID']
LEADERBOARD_SESSION = os.environ['LEADERBOARD_SESSION']
SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
LEADERBOARD_URL = "https://adventofcode.com/{}/leaderboard/private/view/{}".format(
    datetime.datetime.today().year, LEADERBOARD_ID)
LEADERBOARD_USE_LOCAL = bool(os.environ['LEADERBOARD_USE_LOCAL'])
LEADERBOARD_SAVE_LOCAL = bool(os.environ.get('LEADERBOARD_SAVE_LOCAL'))


def get_leader_board():
    """ Grab the Leaderboard from AoC """
    # Allow local JSON to avoid HTTP calls
    if LEADERBOARD_USE_LOCAL:
        with open("local_leaderboard.json") as f:
            return json.load(f)
    r = requests.get("{}.json".format(LEADERBOARD_URL),
                     cookies={"session": LEADERBOARD_SESSION})

    if r.status_code != requests.codes.ok:
        print("Error retrieving leaderboard")

    leaderboard = r.json()

    if LEADERBOARD_SAVE_LOCAL:
        with open("local_leaderboard.json", "w") as f:
            json.dump(leaderboard, f)

    return leaderboard


def build_message(new_stars, team_leaderboard):
    """ Build up the messages to be sent """
    str = ""
    messages = [
        ":star: *{name}* just completed a challenge, they now have *{stars}* stars!\n",
        ":star: Get in! *{name}* just bagged a star. Their total is now *{stars}* stars.\n",
        ":star: DingDing! *{name}* only just went and got a star, that makes *{stars}*.\n",
        ":star: Is it a Bird? Is it a Plane? No, it's *{name}* with *{stars}* stars.\n",
        ":star: BREAKING NEWS: *{name}* is smashing it with *{stars}* stars.\n"
    ]

    for member in new_stars:
        msg = random.choice(messages)
        str += msg.format(name=member['name'], stars=member['stars'])

    if team_leaderboard:
        str += "\n~~~ Team Leaderboard ~~~\n"
        str += "\n" + team_leaderboard

    return str


def get_team_leaderboard(leaderboard, interval=int(os.environ['INTERVAL_HOURS']) * 60 * 60, max_count=5):
    if TEAM_MEMBERS is None:
        print("No TEAM_MEMBERS specified")
        return ""
    leaderboard_members = leaderboard['members']
    # Get all the members we can by team
    teams_members = {
        team_name: [
            leaderboard_members[member_id]
            for member_id in members
            if member_id in leaderboard_members
        ]
        for team_name, members in TEAM_MEMBERS.items()
    }
    # Find all the IDs we know about
    member_ids_in_teams = {
        member['id']
        for members in teams_members.values()
        for member in members
    }
    # Add all other IDs to the 'Unknown' team
    teams_members['Unknown'] = [
        member
        for member_id, member in leaderboard_members.items()
        if member_id not in member_ids_in_teams
    ]
    # Find IDs that are mis-typed or not in the leaderboard
    missing_member_ids = {
        member_id
        for team_name, members in TEAM_MEMBERS.items()
        for member_id in members
        if member_id not in leaderboard_members
    }
    # Warning message
    if missing_member_ids:
        print(
            f"There are {len(missing_member_ids)} member IDs in team "
            f"configuration, that are unknown:")
        print("\n".join(
            f"{member['id']}\t{member['name']}"
            for member_id, member in leaderboard_members.items()
            if member_id in missing_member_ids
        ))
    # Also warning message about unknown
    if teams_members['Unknown']:
        print(f"There are {len(teams_members['Unknown'])} unknown members:")
        print("\n".join(
            f"{member['id']}\t{member['name']}"
            for member in teams_members['Unknown']
        ))
    for name, members in teams_members.items():
        print(f"Team {name} with {len(members)} members:")
        for member in members:
            print(f"  * {member['name']} ({member['id']})")

    # Calculate team scores
    teams_scores = {
        team_name: sum(
            member['stars']
            for member in members
        )
        for team_name, members in teams_members.items()
    }

    team_scores = "\n".join(
        f"{position}. {team_name}: {team_score} "
        f"({len(teams_members[team_name])} members)"
        for position, (team_name, team_score)
        # Sort teams by score, descending
        # Add the position with `enumerate`
        in enumerate(sorted(
            teams_scores.items(),
            key=lambda name_and_score: name_and_score[1], reverse=True), 1)
        # Limit them - if `max_count` is none don't limit
        if max_count is None or position <= max_count
    )
    # Local debugging
    print(team_scores)

    # Find the most recent star
    most_recent_star = max(
        int(member['last_star_ts'])
        for members in teams_members.values()
        for member in members
    )
    # Only add to Slack message if something changed in the last hour
    last_run = int(time.time()) - interval
    if most_recent_star < last_run:
        return ""

    return team_scores


def get_new_stars(leaderboard):
    """ Format the payload of the leaderboard to something more useful, filter to stars only gained since last run """
    last_run = int(time.time()) - int(os.environ['INTERVAL_HOURS']) * 60 * 60
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
    # Allow ignoring posting to Slack, for local
    if SLACK_WEBHOOK == 'ignore':
        return
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
    team_leaderboard = get_team_leaderboard(leaderboard)
    msg = build_message(stars, team_leaderboard)

    print(msg)

    if msg != "":
        send_webhook(msg)


# If running locally
if __name__ == '__main__':
    run(None, None)
