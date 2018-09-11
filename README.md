# twitter-blocklist
A crowdsourced list of undesirable Twitter accounts

For a while now, I've been blocking the authors of every sponsored tweet which appears in my timeline. A recent discussion with friends revealed interest in sharing and crowdsourcing that list, which is why this repository was created.

This list only contains accounts who generate advertising on Twitter. Pull requests to add additional ones are very welcome. New submitters are encouraged so submit screenshots of sponsored tweets in the pull request to speed up the vetting process.

In the future additional blocklists may be created for bot accounts, script kiddies, or generally annoying people.

## How to use
Simply go to your list of [blocked accounts](https://twitter.com/settings/blocked) on Twitter and click "Advanced options" to import the list contained in this repository.

![usage](https://cdn.discordapp.com/attachments/439340562533974026/489082953440165888/unknown.png)

## How to contribute

You are welcome to submit accounts to block! The expected format for entries in the CSV file is: 

```
Twitter ID,Handle,Account Name
```

Twitter's export feature will only generate a list of IDs, so here are a few commands that you can use on a GNU/Linux machine to generate a well-formated file:

```bash
# Get a comma separated list of the IDs to export
cat from_twitter.csv |tr "\n" ","
# See https://github.com/twitter/twurl/; obviously place the IDs you just obtained in the next command
twurl /1.1/users/lookup.json?user_id=1,2,3,4... > /tmp/results.txt
# Generate a CSV from Twitter's JSON
cat /tmp/results.txt |jq '.[] | {id_str, screen_name, name} | join(",")' | tr -d '"' > blocklist.csv
```
