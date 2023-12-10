"""
This script is designed to process tweets from a database, particularly for 
a Twitter bot focused on retweeting content related to the Ukraine war. It 
includes functionalities to check if tweets have been deleted, manage tweet 
status in the database, and perform routine database backups.

The script utilizes the Tweepy library for interacting with the Twitter API 
and TinyDB for database management. It follows a systematic approach to 
ensure each tweet is checked for deletion and its status updated accordingly. 
Additionally, the script handles errors and rate limits efficiently.

Key Functions:
- deleted_check: Determines if a tweet has been deleted.
- check_tweet_list: Processes a list of tweet IDs and updates their status.
- script: Main function to orchestrate tweet processing and database management.

Usage:
Run the script with a specified database name. It will automatically back up 
the database, process tweets, update statuses, and handle new entries.

Dependencies:
- tweepy: For Twitter API interactions.
- tinydb: For local database management.
- shutil: For file operations, including database backup.
"""

import tweepy
from tinydb import TinyDB as tinydb, Query
import time
from war_retweets import backup_database
import shutil

WAIT_TIME = 30
api_key = 'replace this with real info'
api_key_secret = 'replace this with real info'
api_access_token = 'replace this with real info'
api_access_token_secret = 'replace this with real info'
bearer = 'replace this with real info'


def deleted_check(tweet, client):
    """
    Checks if a tweet has been deleted by attempting to retrieve its
    retweeters. Returns True if the tweet is considered deleted.
    """
    time.sleep(WAIT_TIME)
    try:
        temp = client.get_retweeters(tweet)
    except ConnectionResetError as e:
        print(e, flush=True)
        print('Trying again')
        time.sleep(WAIT_TIME)
        client = tweepy.Client(bearer_token=bearer,
                               consumer_key=api_key,
                               consumer_secret=api_key_secret,
                               access_token=api_access_token,
                               access_token_secret=api_access_token_secret,
                               wait_on_rate_limit=True)
        temp = client.get_retweeters(tweet)
        
    if temp.data is None:
        print('0 Retweets, skipping')
        return True
    else:
        test = ['UkraineWarClips' in i.username for i in temp.data]
        if any(test):
            print('Found us, continuing')
            return False
        else:
            print('Didnt find us, not retweeting it.')
            return True


def check_tweet_list(tweet_ids, client, db):
    """
    Processes a list of tweet IDs, updates their status in the database,
    and checks if they have been deleted.
    """
    for tweet_id in tweet_ids:
        try:
            print('\n Processing', tweet_id)
            qu = Query()
            doc = db.search(qu['id'] == tweet_id)
            doc = doc[0] if doc else None
            if not doc:
                db.insert({'id': tweet_id, 'status': 'unchecked'})
            elif 'status' not in doc:
                doc['status'] = 'unchecked'
                db.update(doc, qu['id'] == tweet_id)
            else:
                pass
            deleted = deleted_check(tweet_id, client)
            if not deleted:
                db.update({'status': 'checked'}, qu.id == tweet_id)
            else:
                print(f'\nFound a delete {tweet_id}', flush=True)
                db.update({'status': 'deleted'}, qu.id == tweet_id)
            return deleted
        except Exception as e:
            print(e)


def script(db_name):
    """
    Main script for processing tweets stored in a database. Backs up the
    database, checks each tweet for deletion, and updates their status.
    """
    backup_dir = '/home/josh/backups/'
    backup_database(db_name, backup_dir)
    client = tweepy.Client(bearer_token=bearer,
                           consumer_key=api_key,
                           consumer_secret=api_key_secret,
                           access_token=api_access_token,
                           access_token_secret=api_access_token_secret,
                           wait_on_rate_limit=True)
    new_db = f'{db_name}.delete'
    shutil.copyfile(db_name, new_db)
    db = tinydb(new_db)
    docs_missing_status = [doc for doc in db if 'status' not in doc]
    num_docs = len(docs_missing_status)
    num_processed, start_time, count = 0, time.time(), 0
    for doc in docs_missing_status:
        deleted = check_tweet_list([doc['id']], client, db)
        count += int(deleted)
        num_processed += 1
        num_remaining = num_docs - num_processed
        elapsed_time = time.time() - start_time
        avg_time_per_doc = (elapsed_time / num_processed 
                            if num_processed > 0 else 0)
        estimated_time_remaining = avg_time_per_doc * num_remaining
        print(f"{num_processed} out of {num_docs} processed. "
              f"{num_remaining} remaining. {count = }")
        elapsed_time_str = time.strftime('%H:%M', time.gmtime(elapsed_time))
        est_time_rem_str = time.strftime('%H:%M', 
                                         time.gmtime(estimated_time_remaining))
        print(f"Elapsed time: {elapsed_time_str}. Estimated time remaining: "
              f"{est_time_rem_str}.")
    input('\nPress enter to continue \n')
    print('Copying new docs to', new_db)
    old_db = tinydb(db_name)
    id_set = set(doc['id'] for doc in db)
    for doc in old_db:
        if doc['id'] not in id_set:
            db.insert(doc)
    old_db.close()
    print(f'Done. Rename {new_db} to use.')

if __name__ == '__main__':
    db_name = 'war_retweets_db.json'
    script(db_name)
