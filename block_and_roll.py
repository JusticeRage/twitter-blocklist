#!/usr/bin/env python3
import argparse
import csv
import io
import os
import time

from requests_oauthlib import OAuth1Session
import re
import sys

# Create an app on https://developer.twitter.com/en/portal/dashboard then add
# your consumer key and secret here.
consumer_key = None
consumer_secret = None

# Update these tokens after running the script
access_token = None
access_token_secret = None


###############################################################################
# Usage
###############################################################################

def parse_arguments():
    parser = argparse.ArgumentParser(description="Twitter blocklist management script.")
    parser.add_argument("--generate", "-g", help="Generate a blocklist based on a list of usernames (1 per line).",
                        type=str, metavar='account_list.txt')
    parser.add_argument("--export", "-e", help="Export your blocklist to a CSV file.", action="store_true")
    parser.add_argument("--output", "-o", help="The file in which the generated data will be written. Default: stdout.",
                        type=str, metavar='blocklist.csv')
    parser.add_argument("--import", "-i", help="Import a blocklist in CSV format.", dest="i",
                        type=str, metavar='blocklist.csv')
    args = parser.parse_args()

    if args.generate and not os.path.exists(args.generate):
        print(error("%s does not exist!" % args.generate))
        sys.exit(-1)

    if args.i and not os.path.exists(args.i):
        print(error("%s does not exist!" % args.i))
        sys.exit(-1)

    if args.output and os.path.exists(args.output):
        print(error("%s already exists!" % args.output))
        sys.exit(-1)

    if not args.generate and not args.export and not args.i:
        parser.print_usage()
        print(error("Nothing to do!"))

    return args

###############################################################################
# Pretty printing functions
###############################################################################

GREEN = '\033[92m'
ORANGE = '\033[93m'
RED = '\033[91m'
END = '\033[0m'

def red(text): return RED + text + END
def orange(text): return ORANGE + text + END
def green(text): return GREEN + text + END
def error(text): return "[" + red("!") + "] " + red("Error: " + text)
def warning(text): return "[" + orange("*") + "] Warning: " + text
def success(text): return "[" + green("*") + "] " + green(text)
def info(text): return "[ ] " + text

###############################################################################
# Twitter logic
###############################################################################

def authorize_app():
    global access_token, access_token_secret

    # Get request token
    request_token_url = "https://api.twitter.com/oauth/request_token"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri='oob')

    fetch_response = oauth.fetch_request_token(request_token_url)
    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print("Please go here and authorize: %s" % authorization_url)
    verifier = input("Paste the PIN here: ")

    # Get the access token
    access_token_url = "https://api.twitter.com/oauth/access_token"
    
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    print(f'Please update this script with:\n\taccess_token = "{ oauth_tokens["oauth_token"] }"\n\taccess_token_secret = "{ oauth_tokens["oauth_token_secret"] }"')

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

# -----------------------------------------------------------------------------

global_oauth = None  # Global variable keeping the OAUTH session

def perform_oauth():
    global global_oauth
    if global_oauth is not None:
        return global_oauth

    if access_token is None:
        authorize_app()

    global_oauth = OAuth1Session(consumer_key,
                                 client_secret=consumer_secret,
                                 resource_owner_key=access_token,
                                 resource_owner_secret=access_token_secret)
    return global_oauth

# -----------------------------------------------------------------------------

def perform_request(oauth, url, params=None, verb="GET"):
    if verb == "GET":
        response = oauth.get(url, params=params)
    elif verb == "POST":
        response = oauth.post(url, json=params)
    else:
        raise ValueError("Only GET and POST requests are supported!")

    # Retry later if rate limit was reached.
    while response.status_code == 429:
        print(warning("Rate limiting reached! Trying again in 60 seconds."))
        time.sleep(60)
        if verb == "GET":
            response = oauth.get(url, params=params)
        elif verb == "POST":
            response = oauth.post(url, json=params)

    if response.status_code != 200:
        raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))
    return response.json()

# -----------------------------------------------------------------------------

def resolve_users(usernames):
    oauth = perform_oauth()
    params = {"usernames": ",".join(usernames), "user.fields": "id,username,name"}
    return perform_request(oauth, "https://api.twitter.com/2/users/by", params)

# -----------------------------------------------------------------------------

def get_blocked_accounts():
    oauth = perform_oauth()
    # Get the current user's ID
    user_id = access_token.split('-')[0]

    # Iterate on the blocklist
    blocked_accounts = []
    params = {"max_results": 1000}
    response = perform_request(oauth, f"https://api.twitter.com/2/users/{user_id}/blocking", params)
    blocked_accounts += response["data"]
    while "meta" in response and "next_token" in response["meta"]:
        params = {"max_results": 1000, "pagination_token": response["meta"]["next_token"]}
        response = perform_request(oauth, f"https://api.twitter.com/2/users/{user_id}/blocking", params)
        blocked_accounts += response["data"]
    return blocked_accounts

# -----------------------------------------------------------------------------

def block_account(id):
    oauth = perform_oauth()
    # Get the current user's ID
    user_id = access_token.split('-')[0]

    params = {"target_user_id": id}
    response = perform_request(oauth, f"https://api.twitter.com/2/users/{user_id}/blocking", params, verb="POST")

    if not response["data"]["blocking"]:
        print(error(f"Error encountered while blocking account {id}."))

###############################################################################
# Main
###############################################################################

def generate_blocklist_from_usernames(username_list, stream):
        with open(username_list, "r") as f:
            accounts = f.read().splitlines()
            accounts = list(filter(lambda x: x and not re.match(r"^\s+$", x), accounts))  # Remove empty lines
        if accounts and len(accounts):
            writer = csv.writer(stream, delimiter=",", quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in range(0, len(accounts), 100):
                sublist = accounts[i:i+100]
                api_data = resolve_users(sublist)
                writer.writerows([user["id"], user["username"], user["name"]] for user in api_data["data"])


# -----------------------------------------------------------------------------

def export_blocklist(stream):
    blocked = get_blocked_accounts()
    writer = csv.writer(stream, delimiter=",", quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerows([user["id"], user["username"], user["name"]] for user in blocked)
    print(success(f"Exported {len(blocked)} blocked accounts!"))

# -----------------------------------------------------------------------------

def import_blocklist(blocklist):
    with open(blocklist, "r") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        count = 0
        for row in reader:
            block_account(row[0])
            count += 1
        print(success(f"Added {count} accounts to the blocklist!"))

# -----------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_arguments()

    # Send the output to a CSV file if specified, or to a string buffer.
    if args.output:
        out_stream = open(args.output, "w", encoding='utf-8', newline='')
    else:
        out_stream = io.StringIO()
    try:
        if args.generate:
            generate_blocklist_from_usernames(args.generate, out_stream)
        elif args.export:
            export_blocklist(out_stream)
        elif args.i:
            import_blocklist(args.i)

        # Print the output if no file was specified
        if not args.output:
            print(out_stream.getvalue())
    finally:
        out_stream.close()
