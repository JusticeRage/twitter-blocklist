# twitter-blocklist
A crowdsourced list of undesirable Twitter accounts

For a while now, I've been blocking the authors of every sponsored tweet which appears in my timeline. A recent discussion with friends revealed interest in sharing and crowdsourcing that list, which is why this repository was created.

This list only contains accounts who generate advertising on Twitter. Pull requests to add additional ones are very welcome. There are no plans to curate blocklists for annoying people at the moment, so please make sure that you only include accounts that generate promoted content in the data you submit.

## How to use

In order to work, you will have to **provide Twitter API keys**. To get them you need to [register as a developer](https://developer.twitter.com/en/portal/dashboard) and create a new app. Turn on OAuth 1.0a for it, and you will obtain a `consumer key` and `consumer secret` which need to be inserted in the script `block_and_roll.py` (lines 14 and 15). Then, the first time you run the script, you will need to authorize the app to access your account by pasting a URL in your browser - but from there, all you have to do is follow instructions. I apologize that this process cannot be more simple, but I can't leave my own API keys on GitHub, can I?

Then you can use the script to:
- Export your blocklist into a CSV file and share it with friends. Feel free to send it to me so I can merge it and improve this repository!
- Import the `blocklist.csv` present in this repository. Due to Twitter's rate-limiting on the API, be ready to leave the script running for a few hours.
- Convert a list of twitter handles (one per line) into a proper CSV file that you can then import as a blocklist.

```
usage: block_and_roll.py [-h] [--generate account_list.txt] [--export]
                         [--output blocklist.csv] [--import blocklist.csv]

Twitter blocklist management script.

optional arguments:
  -h, --help            show this help message and exit
  --generate account_list.txt, -g account_list.txt
                        Generate a blocklist based on a list of usernames (1
                        per line).
  --export, -e          Export your blocklist to a CSV file.
  --output blocklist.csv, -o blocklist.csv
                        The file in which the generated data will be written.
                        Default: stdout.
  --import blocklist.csv, -i blocklist.csv
                        Import a blocklist in CSV format.
```
