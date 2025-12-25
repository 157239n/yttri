from k1lib.imports import *

db = sql("dbs/main.db", mode="lite", manage=True)["default"]
db.query("""CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER primary key autoincrement,
    site VARCHAR(50),   /* string code of the site, like 'nhentai' */
    code VARCHAR(50),   /* string code of the episode, commonly a 6 digit number */
    url VARCHAR(200),   /* raw url of the episode overview page if I want to access it raw */
    nPages INT,         /* number of pages total */
    complete BOOL,      /* whether the scanning is complete, all pages are available */
    scanError TEXT,     /* exception message and stack trace, to know what happened */
    createdTime BIGINT, /* unix time of when the episode is created */
    scanTime BIGINT,    /* unix time of when scan is completed */
    quality INT,        /* 1-10 rating, 0 means unrated */
    descr VARCHAR(200), /* short description of the episode, with notable features and whatnot */
    tagIds INT[]        /* fk of the tags table, containing data on tags like 'tentacles', 'bodysuit', 'body swap' */
);""")
# db.query("CREATE INDEX IF NOT EXISTS episodes_code ON users (time);")
db.query("""CREATE TABLE IF NOT EXISTS tags (
    id INTEGER primary key autoincrement,
    name VARCHAR(100)
);""")
db.query("""CREATE TABLE IF NOT EXISTS pages (
    id INTEGER primary key autoincrement,
    episodeId INT,    /* fk with episodes table */
    pageI INT,        /* page number in this episode, 0-indexed */
    url VARCHAR(200), /* raw url of the image */
    complete BOOL,    /* whether image was downloaded successfully */
    content BLOB,     /* raw image content, in jpg */
    hash1 INT,        /* image hashes, to detect similarity between different pages to detect duplicate episodes */
    hash2 INT,
    hash3 INT,
    hash4 INT
);""")
db.query("CREATE INDEX IF NOT EXISTS pages_pageI ON pages (pageI);")
