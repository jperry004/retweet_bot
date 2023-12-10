#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A Twitter bot designed to retweet videos related to the Ukraine war, using
Twitter API. It filters tweets based on content relevance, avoiding
inappropriate or redundant content, and incorporates tie detection in videos
as part of its evaluation process.

Features:
- Automated search for Ukraine war-related video tweets.
- Filtering based on bad words, author uniqueness, content sameness.
- Tie detection in videos.
- Retweeting validated tweets and storing information in TinyDB.
- Fibonacci-based retry mechanism for rate limits and exceptions.

Dependencies:
- tweepy, requests, TinyDB, tie_detector module.

Usage:
Run the script to initiate the bot. It operates in a continuous loop, handling
search, evaluation, retweeting, and error management.

Author: Josh Perry
Created: March 16, 2022
"""


import re
import os
import time
import tweepy
import requests
from shutil import copyfile
from datetime import datetime
from tinydb import TinyDB as tinydb, Query
from tie_detector import tie_detector, download_tweet_video

fibonacci_index = 7
SAMENESS_RATIO = 0.7
RETWEET_LIMIT_SEC = 1320 # 22 minutes  
BADS = ['mq-9', 'sadam', 'erbil', 'iraq', 'iran', 'osama', 'nft', '#nft', 
        'podcast', 'biden', 'ww3', 'hillary', 'trump', 'queen', 
        'pakistan', 'taliban', 'lavrov', 'ccp', 'communist', 'anything', 
        'konashenkov', 'marjorie', 'uysk', 'mq', 'removed', 'somalia',
        'boxer', 'sudan']

api_key = 'replace this with real info'
api_key_secret = 'replace this with real info'
api_access_token = 'replace this with real info'
api_access_token_secret = 'replace this with real info'
bearer = 'replace this with real info'
fibonacci = lambda n: int(((1 + 5**0.5) / 2)**n / 5**0.5 + 0.5)



def matches_finder(tweet, db):
    """
    Searches a database for tweets matching the given tweet by media key, ID, 
    or duration.
    Outputs relevant messages and returns True if a match is found, else False.
    
    Args:
    - tweet (dict): A dictionary containing details of the tweet to match.
    - db (TinyDB): The database instance to search in.
    
    Returns:
    - bool: True if a match is found, False otherwise.
    """
    Tweet = Query()
    mkey, duration, tid = tweet.get('media_key'), tweet.get('duration_ms'), 
    tweet.get('id')
    
    matches = db.search((Tweet.media_key == mkey) | (Tweet.id == tid) )
    dur_matches = db.search(Tweet.duration_ms == duration)
    
    if matches:
        print('Found non-duration match')
        return True
    
    elif dur_matches:
        if tweet.get('duration_ms') == dur_matches[0].get('duration_ms'):
            print('\nMatched duration', tid, dur_matches[0].get('id'))
            try:
                new = download_tweet_video(tid)
                old = download_tweet_video(dur_matches[0].get('id'))
            except AssertionError as e:
                print('DL failed, returning False', e)
                return False
            error = compare_file_sizes(new, old)
            os.remove(old)
            if error:
                return error < 10
            else: return False
    else:
        return False
            
def compare_file_sizes(file1, file2):
    """
    Compares the file sizes of two files and calculates the percentage 
    difference.
    
    Args:
    - file1 (str): Path to the first file.
    - file2 (str): Path to the second file.
    
    Returns:
    - float or None: The percentage difference in file sizes, or None if 
    either file is empty.
    """
    size1 = os.path.getsize(file1)
    size2 = os.path.getsize(file2)
    if size1 == 0 or size2 == 0:
        return None
    error = abs(size1 - size2) / size1 * 100
    print(f'\nFilesize error: {int(error)}')
    return error

def bearer_oauth(r):
    """
    Function required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

def connect_to_endpoint(url, params):
    '''
    Function to get response from end point.
    '''    
    response = requests.get(url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

    
def sameness_efficient(tweet, db):
    """
    Evaluates if a given tweet is similar to any previously stored tweets in 
    a database based on word overlap.

    This function compares the words in the given tweet against the words in 
    tweets stored in the database. It calculates the ratio of the longest 
    common word set to the total number of words in the tweet. If this ratio 
    exceeds a predefined threshold (SAMENESS_RATIO), 
    the function indicates a 'sameness alert'.

    Args:
    - tweet (str): The tweet text to be evaluated.
    - db (list): A list of dictionaries, where each dictionary represents a 
    tweet with a 'words' key.

    Returns:
    - bool: True if the sameness ratio exceeds the predefined threshold, 
    False otherwise.
    """
    tweet_words = set(tweet.lower().split())
    previous_tweets = [set(x.get('words')) for x in db]
    longest_previous = max(len(tweet_words & y) for y in previous_tweets)
    ratio = longest_previous / len(tweet_words)
    if ratio > SAMENESS_RATIO: 
        print('\nSameness alert\n{}\n{}'.format(ratio, tweet))
        return True
    else:
        print('\nSameness ratio:', ratio)
        return False
    
def deleted_check(tweet, db):
    """
    Checks if a significant percentage of an author's previous tweets have 
    been deleted.
    
    This function searches a database for tweets by the same author and 
    calculates the percentage of those tweets that have been marked as 
    'deleted'. Depending on the number of previous tweets, different 
    thresholds are applied to determine if a significant percentage of tweets 
    have been deleted.
    
    Args:
    - tweet (dict): A dictionary containing the tweet data, including the 
    'author_id'.
    - db (TinyDB): The database instance to search in.
    
    Returns:
    - bool: True if the deletion percentage exceeds the set threshold, False 
    otherwise.
    """
    # Create a query object
    qu = Query()
    # Search the database for previous tweets with the same ID 
    previous_tweets = db.search(qu['author_id'] == tweet.get('author_id'))
    
    # If there are no previous tweets with the same ID return False
    if not previous_tweets:
        print('\nNo previous tweets, retweeting')
        return False
    
    # Otherwise, print a message and check the previous tweets for deletions
    else:
        print(f'\nChecking previous {len(previous_tweets)} tweets for deletes')
        delete_count = 0
        
        # Loop through the previous tweets
        for previous in previous_tweets:
            previous_status = db.get(qu['id'] == previous['id']).get('status')
            
            # If the status field is 'deleted', increment the delete count
            if previous_status == 'deleted':
                delete_count += 1
            
        # Calculate the percentage of previous tweets that were deleted
        delete_percentage = int((delete_count / len(previous_tweets)) * 100)
        print(f'\n{delete_percentage}% of previous tweets have been deleted')
        # Return True if the delete percentage is > threshold, otherwise False
        if len(previous_tweets) <= 3:
            threshold = 50
        elif len(previous_tweets) <= 10:
            threshold = 25
        else:
            threshold = 10
        return delete_percentage > threshold
 
def backup_database(db_filename, backup_dir):
    """
    Back up a TinyDB database to a file in the specified backup directory.
    """
    now = datetime.now()
    backup_filename = (
        f"{os.path.basename(db_filename)}_"
        f"{now.strftime('%Y-%d-%m')}.bak")    

    backup_path = os.path.join(backup_dir, backup_filename)
    copyfile(db_filename, backup_path)
    print(f"Database backed up to {backup_path}", flush=True)

    # Get a list of all .bak files in the directory
    bak_files = [f for f in os.listdir(backup_dir) if f.endswith(".bak")]
    
    # If there are more than 7 .bak files, delete the oldest ones 
    if len(bak_files) > 7:
        # Sort the .bak files by creation time (most recent first)
        bak_files.sort(
            key=lambda f: os.path.getctime(os.path.join(backup_dir, f)),
            reverse=True)        
        # Delete the oldest files until there are only 7 left
        for file_to_delete in bak_files[7:]:
            os.remove(os.path.join(backup_dir, file_to_delete))
            print(f"Deleted backup file: {file_to_delete}")

                    
def script():
    """
     Automates the process of finding, evaluating, and retweeting tweets 
     related to the Russia-Ukraine conflict.
    
     This script searches for tweets with videos related to the conflict, 
     using specified search terms. It then performs various checks to ensure 
     tweet relevance and uniqueness, avoiding duplicates or irrelevant content. 
     Valid tweets are retweeted and stored in a database.
    
    
     The script runs in loops, each time fetching and processing a new set of 
     tweets until a specified limit is reached.
     """
     
     
    # define the search terms for finding videos
    q = (
    	'(russia OR russian OR ukraine OR ukrainian OR Россия OR русский OR '
    	'Украина OR украинец OR Росія OR російський OR Україна OR українець) '
    	'(troops OR forces OR attack OR ambush OR shelling OR fight OR '
    	'fighting OR capture OR войска OR сила OR атака OR засада OR обстрел '
    	'OR борьба OR боевые действия OR захватывать OR війська OR сила OR '
    	'атакувати OR засідка OR обстріл OR боротьба OR бойові дії OR '
    	'захопити) has:videos -is:retweet -is:verified'
    )

    users = []
    db_filename = 'war_retweets_db.json'
    backup_dir = '/home/josh/backups/'
    # fill the database 
    db = tinydb(db_filename)
    print(f'\nLoaded {len(db)} previous retweets', flush=True)
    for loops in range(5):
        # setup client
        client = tweepy.Client(bearer_token = bearer,
                   consumer_key = api_key,
                   consumer_secret = api_key_secret,
                   access_token = api_access_token,
                   access_token_secret = api_access_token_secret,
                   wait_on_rate_limit=True)    

        search_url = "https://api.twitter.com/2/tweets/search/recent"
        # Optional params: start_time,end_time,since_id,until_id,max_results,
        # expansions,tweet.fields,media.fields,poll.fields,place.fields,
        # next_token,user.fields
        query_params = {'query': q,
                        'expansions': 'attachments.media_keys,author_id',
                        'media.fields': 'duration_ms',
                        'max_results': '100'}
        time.sleep(10)
        json_response = connect_to_endpoint(search_url, query_params)
        
        # add media data to tweet dict
        allTweets = []
        _tweets = json_response.get('data')
        includes_media = json_response.get('includes').get('media')
        # check that each tweet does in fact have a video
        for tweet in _tweets:
            attachments = tweet.get('attachments')
            if attachments:
                media_key = attachments.get('media_keys')
                media_data = [x for x in includes_media if 
                              x.get('media_key') == media_key[0]]
                if media_data:
                    temp = tweet.copy()
                    temp.update(media_data[0])
                    temp['timestamp'] = int(time.time())
                    temp['words'] = temp.get('text').lower().split()
                    allTweets.append(temp)
                else:
                    print('no media data')
            else:
                print('no attachs')
        # define a list of words to avoid          
        bads = BADS + [x + 's' for x in BADS]
        sent = 0
                 
        for tweet in allTweets:
            print('\nProcessing:', tweet, flush=True)
            # check if the tweet id, media_key, duration is already in the db.
            tweet_id = tweet.get('id')
            previous_deletes = deleted_check(tweet, db)
            if previous_deletes:
                print('\nSkipping, too many previous deletes', tweet_id, '\n')
                continue
            bad_test = [not not re.findall(x, 
                                    tweet.get('text').lower()) for x in bads]
            # check if there's any reason to reject the tweet
            easys = [tweet.get('author_id') in users, 
                     sameness_efficient(tweet.get('text'), db), any(bad_test), 
                     tweet.get('type') != 'video']
            if any(easys):
                print('\nSkipping', tweet_id, '\n')
                categories = (
                    'Author, Sameness, Bad Words, Not Video'
                    .split(', '))
                results = "\n".join(f"{a:.^15} {b}\n" for a, b 
                                    in zip(categories, easys))
                print(results)                
                continue
            matches = matches_finder(tweet, db)
            if matches:
                print('\nMatches - skipping', tweet_id, '\n')
                continue
            try:
                tie_seen = tie_detector(tweet_id)            
            except Exception as e:    
                tie_seen = False
                print(e)
            bool_list = [matches, previous_deletes, tie_seen]
            tests = easys
            tests.extend(bool_list)
            categories = (
                'Author, Sameness, Bad Words, Not Video, Matches, '
                'Pr. Deletes, Tie Seen'.split(', ')
            )
            results = "\n".join(
                f"{a:.^15} {b}\n" for a, b in zip(categories, tests)
            )

            print(results)                
            if tie_seen:
                print('\nTie seen - skipping', tweet_id, '\n')
                continue
            # if no reason to reject then add it to the db, retweet, and wait
            if not any(tests):
                users.append(tweet.get('author_id'))
                try:                    
                    db.insert(tweet)
                    client.retweet(tweet_id)
                    print('\nRetweeted', tweet_id)
                    sent += 1
                    print('\nSent {} of {}'.format(sent, len(allTweets)))
                    now = datetime.now().strftime("%H:%M:%S")
                    print("\nCurrent Time =", now)
                    # back it up if it's midnight
                    if datetime.now().hour == 4:
                        backup_database(db_filename, backup_dir)
                        global fibonacci_index
                        fibonacci_index = 7
                    print(f'\nWaiting {RETWEET_LIMIT_SEC} seconds', flush=True)
                    time.sleep(RETWEET_LIMIT_SEC)
                except tweepy.errors.BadRequest as e:
                    print(e, flush=True)
    
                except ConnectionResetError as e:
                    print(e, flush=True)
                    print('Trying again')
                    client = tweepy.Client(bearer_token = bearer,
                       consumer_key = api_key,
                       consumer_secret = api_key_secret,
                       access_token = api_access_token,
                       access_token_secret = api_access_token_secret,
                       wait_on_rate_limit=True)   
                    client.retweet(tweet_id)


            if sent > 10: break

if __name__ == '__main__':
    

    # run the script forever and on an exception wait fibonacci mins to retry
    while 1:
        try:
            script()
        except Exception as e:
            wait = fibonacci(fibonacci_index)
            print(f'Waiting {wait} mins bc:', e, flush=True)
            time.sleep(wait*60)
            fibonacci_index += 1
            



