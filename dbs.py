from k1lib.imports import *

db = sql("dbs/main.db", mode="lite", manage=True)["default"]
"""
Qualities:
- 3:  never want to see again, can safely delete
- 5:  meh, no memories, no impressions
- 6:  not in my territory, but I can respect it
- 7:  pretty nice, decent, in my territory
- 8:  ok this is kinda good
- 9:  fuck this is so good
- 10: literal orgasm every time
"""
db.query("""CREATE TABLE IF NOT EXISTS eps (
    id          INTEGER primary key autoincrement,
    site        TEXT,    -- string code of the site, like 'nhentai'
    code        TEXT,    -- string code of the episode, commonly a 6 digit number
    url         TEXT,    -- raw url of the episode overview page if I want to access it raw
    createdTime BIGINT,  -- unix time of when the episode is created
    nPages      INTEGER, -- number of pages total
    urls        TEXT[],  -- array of all image urls by scanning zircon
    errUrls     TEXT,    -- error while fetching for page urls. None if not started, '' if successful
    quality     INTEGER, -- 1-10 rating, 0/null means unrated. Quality numbers listed above
    descr       TEXT,    -- short description of the episode, with notable features and whatnot
    tagIds      INT[]    -- fk of the tags table, containing data on tags like 'tentacles', 'bodysuit', 'body swap'
);""")
db.query("""CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER primary key autoincrement,
    name TEXT
);""")
db.query("""CREATE TABLE IF NOT EXISTS pages (
    id       INTEGER primary key autoincrement,
    epId     INTEGER, -- fk with episodes table
    pageI    INTEGER, -- page number in this episode, 0-indexed
    url      TEXT,    -- raw url of the image
    imgB     BLOB,    -- raw image content, in jpg
    errImg   TEXT,    -- error while fetching image. None if not started, '' if successful
    hash1    INTEGER, -- image hashes, to detect similarity between different pages to detect duplicate episodes
    hash2    INTEGER,
    hash3    INTEGER,
    hash4    INTEGER,
    errHash  TEXT     -- error while grabbing image hashes. None if not started, '' if successful
);""")
db.query("CREATE INDEX IF NOT EXISTS pages_epId ON pages (epId);")
db.query("CREATE INDEX IF NOT EXISTS pages_pageI ON pages (pageI);")
db.query("CREATE INDEX IF NOT EXISTS pages_hash1 ON pages (hash1);")
db.query("CREATE INDEX IF NOT EXISTS pages_hash2 ON pages (hash2);")
db.query("CREATE INDEX IF NOT EXISTS pages_hash3 ON pages (hash3);")
db.query("CREATE INDEX IF NOT EXISTS pages_hash4 ON pages (hash4);")
# db.query("CREATE INDEX IF NOT EXISTS episodes_code ON users (time);")
