# RSS to Google Keep

This repository provides a simple Python script to add RSS items
to one's [Google Keep](https://keep.google.com) notes.

This is intended to be dead-simple, rather than full-featured.

## Getting started

In this directory, create a new file `run.py`, and set its content to:

```py
import rsstokeep

# Add an RSS feed to listen to.
# Items imported from this feed will be saved in the data.yml file,
# and therefore restarting the script will NOT duplicate items.
# The 'interval' parameter specifies that we'll check for new items every hour.
rsstokeep.add_feed('XKCD', 'https://xkcd.com/rss.xml', interval=3600)

# Run the main loop.
rsstokeep.run()
```
