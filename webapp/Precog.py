from __future__ import division
import tweepy
import json
import re
import pycountry
import matplotlib.pyplot as plt
from pymongo import MongoClient
from textblob import TextBlob
from wordcloud import WordCloud
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import googlemaps
import pickle
from textblob import TextBlob
import os

#MongoDB stuff

client=MongoClient('localhost:27017')
db=client.Precog
collection=db.Mumbai

###
c=0
#keys=['AIzaSyD1ubxPRDmcB27yLnBf5gwcr1sWhK-d_uQ','AIzaSyD2fr6YNEstMtDb4dqfaUEPkHIjHgoPhoc','AIzaSyAMwMnZCv69oU0jIHpY1w08317Aq1JMeyA','AIzaSyDRwA51F4MwEO0QZ3ighneycI8CmRgWNZQ','AIzaSyAord1o3WYoFev71mRatDeNlVT4-YmTwBs','AIzaSyD-NL5a-SBeyuHb0hEEE8to8tKFBwFiQM8']
keys=['AIzaSyDHH54aJBGIOtdbx2G-OubBLeIPmZhYFQY','AIzaSyDWNAHmkLHn607a5rOKMcSm0HN1coKduRs','AIzaSyBMInX8YLhBSi7-gCIQilvwjmaBm8b0YsI','AIzaSyB19nINy5cRB43mZHlJFJM0vW739L8UZrk','AIzaSyCwXQup86YB0ckzjVWASM9iaSqSEddgmUg','AIzaSyCei5QUi3UTfL39CBlqWXqUYu4WwgHd2fs']
gmaps = googlemaps.Client(key=keys[0])

'''
to load

with open ('outfile', 'rb') as fp:
    itemlist = pickle.load(fp)

to write

with open('outfile', 'wb') as fp:
    pickle.dump(itemlist, fp)

'''

def make_graph():
    itera=collection.find()
    links=[]
    #1 for mention 2 for retweet 3 for reply
    for t in itera:
        if ('user_mentions' in t['entities']):
            for k in t['entities']['user_mentions']:
                links.append([t['user']['screen_name'],k['screen_name'],1])

        if('retweeted_status' in t):
            links.append([t['retweeted_status']['user']['screen_name'],t['user']['screen_name'],2])

        if(t['in_reply_to_user_id_str']):
            links.append([t['user']['screen_name'],t['in_reply_to_screen_name'],3])

    print links

    with open('Delhi-graph', 'wb') as fp:
        for s in links:
            s=[str(e) for e in s]
            fp.write(' '.join(s) + '\n')


def clean_tweet(s):
	return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ",s).split())

def get_sentiment(text):
	analysis = TextBlob(clean_tweet(text))
	return analysis.sentiment.polarity

def get_hash(tweets):
    tags=[]
    for t in tweets:
        for k in t._json['entities']['hashtags']:
            tags.append(k['text'].encode('utf-8'))
    return tags

def get_polarity(tweets):
    total=0.0
    count=[0,0]
    for tweet in tweets:
        if(tweet._json['lang']=='en'):
            if get_sentiment(tweet._json['text'])>0:
                count[0]+=1
            elif get_sentiment(tweet._json['text'])<0:
                count[1]+=1
    return count

def non_users():
    itera=collection.find()
    non_users=[]
    for t in itera:
        if(t['user']['location']):
            s=t['user']['location'].encode('utf-8')
            if('delhi' not in s.lower() and not ('retweeted_status' in t)):
                non_users.append(t['user']['id']) #has the user_id
    print len(non_users)
    finallist=[]
    hashtags=[]
    for i in non_users:
        try:
            some=api.get_user(i)
            tweets=api.user_timeline(i)
            if(some._json['friends_count']==0):
                density=0.0
            else:
                density=some._json['followers_count']/some._json['friends_count']
            polarity=get_polarity(tweets)
            if(get_hash(tweets)!=[]):
                hashtags.extend(get_hash(tweets))
            print density,polarity
            finallist.append([density,polarity[0],polarity[1]])
        except:
            pass
    print finallist

    with open('Non-Mumbai-related', 'wb') as fp:
        for s in finallist:
            s=[str(e) for e in s]
            fp.write(' '.join(s) + '\n')

    hashtags=[s.lower() for s in hashtags]
    hashtags=set(hashtags)
    query=['MumbaiRains','CycloneOckhi','MumbaiRain','Ockhi','mumbaiweather','cycloneinmumbai','mumbaiweatherupdate']
    #query=['Smog','MyRightToBreathe','CropBurning','delhipollution','delhismog','delhiairpollution','stubbleburning','SmogInDelhi','delhigaschamber','DelhiChokes','letdelhibreathe']
    query=[q.lower() for q in query]
    for q in query:
        hashtags.discard(q)
    print hashtags

    with open('Non-Mumbai-related-hashtags', 'wb') as fp:
        for s in hashtags:
            s=[str(e) for e in s]
            fp.write(' '.join(s) + '\n')


def location():
    itera=collection.find()
    location=[]
    counter=0
    last=0
    coordinates=[]
    global c
    global keys
    for t in itera:
        if(t['user']['location'] and t['in_reply_to_user_id_str'] and 'retweeted_status' not in t):
            print counter
            s=t['user']['location']
            s=s.split(',')
            if(len(s)==1 and 'india' in s[0].lower()):
                continue
            try:
                location.append(t['user']['location'])
                geocode = gmaps.geocode(location[-1])
                if(geocode!=[]):
                    comp=geocode[0]['address_components']
                    for c in comp:
                        if(c['types']==["country", "political"]):
                            country=c['long_name'].encode('utf-8')
                        if(c['types']==[ "administrative_area_level_1", "political" ]):
                            state=c['long_name'].encode('utf-8')
                    coordinates.append([geocode[0]['geometry']['location']['lat'],geocode[0]['geometry']['location']['lng'],state,country])
                    print coordinates[-1]
                    counter+=1
            except:
                if(c==0):
                    with open('Mumbai-new', 'wb') as fp:
                        for s in coordinates:
                            fp.write(''.join(s) + '\n')
                    last=len(coordinates)
                else:
                    with open('Mumbai-new', 'a') as fp:
                        for s in coordinates[last:]:
                            fp.write(''.join(s) + '\n')
                        last=len(coordinates)
                gmaps = googlemaps.Client(key=keys[c+1])
                c+=1

    with open('Mumbai-new', 'a') as fp:
        for s in coordinates:
            s=[str(e) for e in s]
            fp.write(' '.join(s) + '\n')

def hashtags():
    itera=collection.find()
    hashtags={}
    hashes=[]
    for t in itera:
        if(t['lang']!='en'):
            continue
        temp=t['entities']['hashtags']
        if(temp):
            for i in range(len(temp)):
                s=temp[i]['text'].lower()
                if(s not in hashes):
                    hashes.append(s)
                    hashtags[s]=1
                else:
                    hashtags[s]=hashtags[s]+1
    hashtags_r = sorted(hashtags, key=hashtags.get, reverse=True)
    count=0
    for i in hashtags_r:
        if(count>10):
            break
        else:
            print i,hashtags[i]
        count=count+1


    wordcloud = WordCloud()
    wordcloud.generate_from_frequencies(frequencies=hashtags)
    image = wordcloud.to_image()
    image.save('./webapp/static/project_pre/images/WordCloud.png')

def tweet_retweet_distribution():
	itera=collection.find()
	types=['Tweets','Retweets']
	count=[0,0]
	for t in itera:
		if('retweeted_status' in t):
			count[1]=count[1]+1
		else:
			count[0]=count[0]+1
	finallist=[[types[0],count[0]],[types[1],count[1]]]


def get_favcount():
	itera=collection.find()
	fav_count_tweets={} #Dictionary to store the tweets with the fav count
	total=0
	fav_count=0
	for t in itera:
		total=total+t['user']['favourites_count']
		if('retweeted_status' not in t):
			fav_count_tweets[t['id']]=t['user']['favourites_count']
			fav_count=fav_count+t['user']['favourites_count']
	print fav_count,total
	explode=[0,0]
	count=[fav_count,total-fav_count]
	types=['Original','Retweeted']
	finallist=[[types[0],count[0]],[types[1],count[1]]]

def tweet_type():
    itera=collection.find()
    types=['Text','Text+Images','Images']
    count=[0,0,0]
    for t in itera:
        if('media' in t['entities'] and t['text']):
            count[1]+=1
        elif('media' in t['entities']):
            count[2]+=1
        else:
            count[0]+=1
    finallist=[[types[0],count[0]],[types[1],count[1]],[types[2],count[2]]]
    print finallist



def collect_data():

    #query='#Smog OR #MyRightToBreathe OR #CropBurning OR #delhipollution OR #delhismog OR #delhiairpollution OR #stubbleburning OR #SmogInDelhi OR #delhigaschamber OR #DelhiChokes OR #letdelhibreathe'
    query='#MumbaiRains OR #CycloneOckhi OR #MumbaiRain OR #Ockhi OR #mumbaiweather OR #cycloneinmumbai OR #mumbaiweatherupdate'
    maxTweets=12000
    counter=0
    Tweets=[]
    counter=0

    for tweet in tweepy.Cursor(api.search,q=query).items(maxTweets):
        t=tweet._json
        print t['id']
        if(t['id'] in listx):
            counter+=1
            continue
        else:
            listx.append(t['id'])
            Tweets.append(t)

    print counter
    print(len(Tweets))

    collection.insert(Tweets)


def make_json(string):
    file_name = '{}-graph'.format(string)
    f=open(file_name, 'r')
    lister=f.readlines()
    val={}
    users=[]
    counter=0
    val["nodes"]=[]
    val["links"]=[]
    for item in lister:
        link={}
        if(counter>1000):
            break
        item=item.strip('\n')
        item=item.split(' ')
        if not (item[0] in users ):
            users.append(item[0])
            val["nodes"].append({"name":item[0],"group":item[2]})

        if not (item[1] in users):
            users.append(item[1])
            val["nodes"].append({"name":item[1],"group":item[2]})

        link["source"]=item[0]
        link["target"]=item[1]

        if(item[2]==1):
            link["value"]=1
        elif(item[2]==2):
            link["value"]=10
        else:
            link["value"]=4

        val["links"].append(link)
        counter+=1

    print val
    with open('{}.json'.format(string), 'w') as fp:
        json.dump(val, fp)


ckey='cr2cyj7xBC2GBbzpHuaJRv0PD'
csecret='eEflWUxJZqM3FR56qMlGUATW4JvwfQwMzfDsuOtrMrLPZoI8DV'
atoken='892379507994144768-rwy5OSGnGy8xWlIjWWq26y4ZmJHhhpf'
asecret='6OmcTSrArPsi6SkrknWh8ULCBBGwEEcQu826Lxk6mJxoK'

auth =tweepy.AppAuthHandler(ckey,csecret)
api = tweepy.API(auth,wait_on_rate_limit=True,wait_on_rate_limit_notify=True)

#non_users()
#make_graph()
#location()
make_json('Delhi')
