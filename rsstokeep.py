import gkeepapi, os, time, yaml


# Load Google Keep and saved data

keep = gkeepapi.Keep()

if os.path.isfile('data.yml'):
    with open('data.yml') as f:
        data = yaml.load(f.read())

    keep.resume(data['email'], data['token'])
else:
    from getpass import getpass

    while True:
        email = input('[?] Email: ')
        password = getpass('[?] Password: ')

        if keep.login(email, password):
            break

    data = { 'email': email, 'token': keep.getMasterToken(), 'feeds': {} }

print('[+] Successfully logged in.')


# Schedule feed updates and sync items

feeds = []

def save_state():
    with open('data.yml', 'w') as f:
        f.write(yaml.dump(data, default_flow_style=False))

def add_feed(name, url, interval=3600, filter=None, selector=None, key=None, start_date=None):
    if key is None:
        key = name

    feed = data['feeds'].get(key)

    if feed is None:
        feed = { 'name'    : name,
                 'url'     : url,
                 'id'      : None,
                 'interval': interval,
                 'lastItemDate': time.time() if start_date is None else start_date
               }
        data['feeds'][key] = feed

    feeds.append((feed, filter, selector))

def sync_feed(feed, filter, selector):
    import feedparser

    if filter is None:
        filter = lambda x: True
    if selector is None:
        selector = lambda x: x.title + ': ' + x.link

    try:
        rss = feedparser.parse(feed['url'])
    except e:
        print('[-] Could not sync feed', feed['name'], '; will retry later.')
        return

    added = 0
    min_date = feed['lastItemDate']

    for entry in rss.entries:
        entry_date = time.mktime(entry.published_parsed)

        if entry_date <= min_date or not filter(entry):
            continue

        data = selector(entry)

        if data is None:
            continue

        added += 1

        if isinstance(data, str):
            # String, we simply add a list item
            if feed['id'] is None or keep.get(feed['id']) is None:
                note = keep.createList(feed['name'], [ (data, False) ])
                feed['id'] = note.id
            else:
                note = keep.get(feed['id'])
                note.add(data, False)

        else:
            # Object, we create a new note altogether
            note = keep.createNote(data['title'], data['text'])

            if 'labels' in data:
                for label in data['labels']:
                    note.labels.add(get_label(label))

        feed['lastItemDate'] = max(feed['lastItemDate'], entry_date)

    if added == 0:
        return

    try:
        keep.sync()
        print('[+] Added', added, 'feed item(s) from', feed['name'], 'to Keep.')
    except e:
        print('[-] Could not sync changes to Keep ; will retry later.')

    save_state()

def run(now=True):
    import schedule, signal, sys

    for feed, filter, selector in feeds:
        def run_job():
            sync_feed(feed, filter, selector)

        schedule.every(feed['interval']).seconds.do(run_job)

        if now:
            sync_feed(feed, filter, selector)

    running = True

    def handle_sigint(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_sigint)

    while running:
        schedule.run_pending()
        time.sleep(1)


# Some utils

def get_label(name):
    label = keep.findLabel(name)

    if label is None:
        label = keep.createLabel(name)

    return label
