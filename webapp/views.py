# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse

from django.views.generic import TemplateView
import pickle
import tweepy
import json
import os
import re
import matplotlib.pyplot as plt
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
from pymongo import MongoClient
from textblob import TextBlob
from wordcloud import WordCloud

client=MongoClient('localhost:27017')
db=client.Precog
collection=db.Mumbai
collection2=db.Delhi

def index(request):
	return render(request,'index.html')

def view_network_delhi(request):
	return render(request,'network_delhi.html')

def view_network_mumbai(request):
	return render(request,'network_mumbai.html')

def view_non_users(request):
	delhi_users=json.dumps(get_users('Delhi'))
	delhi_sentiment=json.dumps(get_sentiment('Delhi'))
	delhi_wordcloud=json.dumps(make_wordcloud('Delhi'))
	Mumbai_users=json.dumps(get_users('Mumbai'))
	Mumbai_sentiment=json.dumps(get_sentiment('Mumbai'))
	Mumbai_wordcloud=json.dumps(make_wordcloud('Mumbai'))

	return render(request,'nonusers.html',{"data10":delhi_users,"data11":delhi_sentiment,"data20":Mumbai_users,"data21":Mumbai_sentiment})

def get_users(string):
	file_name = os.path.dirname(__file__) + '/Non-{}-related'.format(string)
	f=open(file_name, 'r')
	lister=f.readlines()
	counter=0
	count=0
	for item in lister:
		item=item.strip('\n')
		item=item.split(' ')
		if(float(item[0].encode('utf-8'))>10.0):
			count+=1
		counter+=1
	print count,counter
	return [['Popular',count],['Common',counter-count]]

def get_sentiment(string):
	file_name = os.path.dirname(__file__) + '/Non-{}-related'.format(string)
	f=open(file_name, 'r')
	lister=f.readlines()
	positive=0
	negative=0
	for item in lister:
		item=item.strip('\n')
		item=item.split(' ')
		positive+=int(item[1].encode('utf-8'))
		negative+=int(item[2].encode('utf-8'))
	return [['Positive',positive],['Negative',negative]]

def make_wordcloud(string):
	file_name = os.path.dirname(__file__) + '/Non-{}-related-hashtags'.format(string)
	f=open(file_name, 'r')
	count=0
	lister=f.readlines()
	hashtags={}
	for item in lister:
		if(count>10):
			break
		item=item.strip('\n')
		item=item.strip(' ')
		hashtags[item]=20-2*count+1
		count+=1

	wordcloud = WordCloud()
	wordcloud.generate_from_frequencies(frequencies=hashtags)
	image = wordcloud.to_image()
	image.save('./webapp/static/images/{}-nonusers.png'.format(string))

def view_type(request):
	delhi=json.dumps(tweet_type(collection2))
	mumbai=json.dumps(tweet_type(collection))
	return render(request,'tweet_type.html',{"data1":delhi,"data2":mumbai})

def tweet_type(collection):
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
    return finallist

def view_favcount(request):
	delhi=json.dumps(get_favcount(collection2))
	mumbai=json.dumps(get_favcount(collection))
	return render(request,'favcount.html',{"data1":delhi,"data2":mumbai})

def get_favcount(collection):
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
	return finallist

def view_tweetretweet(request):
	delhi=json.dumps(tweet_retweet_distribution(collection2))
	mumbai=json.dumps(tweet_retweet_distribution(collection))
	return render(request,'tweetretweet.html',{"data1":delhi,"data2":mumbai})

def tweet_retweet_distribution(collection):
	itera=collection.find()
	types=['Tweets','Retweets']
	count=[0,0]
	for t in itera:
		if('retweeted_status' in t):
			count[1]=count[1]+1
		else:
			count[0]=count[0]+1
	finallist=[[types[0],count[0]],[types[1],count[1]]]
	return finallist

def view_hashtags(request):
	delhi=hashtags(collection2,'delhi')
	mumbai=hashtags(collection,'mumbai')
	return render(request,'hashtags.html')

def hashtags(collection,string):
	itera=collection.find()
	hashtags={}
	hashes=[]
	top={}
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
		if(count>30):
			break
		else:
			print i,hashtags[i]
			top[i]=hashtags[i]
		count=count+1
	wordcloud = WordCloud()
	wordcloud.generate_from_frequencies(frequencies=top)
	image = wordcloud.to_image()
	image.save('./webapp/static/images/{}.png'.format(string))

def view_location(request):
	delhi=json.dumps(location('Delhi'))
	mumbai=json.dumps(location('Mumbai'))
	return render(request,'location.html',{"data1":delhi,"data2":mumbai})

def location(string):
	file_name = os.path.dirname(__file__) + '/{}-new'.format(string)
	f=open(file_name, 'r')
	lister=f.readlines()
	loc={}
	finallist=[]
	for item in lister:
		try:
			item=item.split(' ')
			if(item[2] in loc.keys()):
				loc[item[2]]+=1
			else:
				loc[item[2]]=1
		except:
			pass
	for k in loc:
		finallist.append([k,loc[k]])
	print finallist
	return finallist

def view_network(request):
	make_json('Delhi')
	#make_json('Mumbai')
	return render(request,'network.html')

def make_json(string):
	file_name = os.path.dirname(__file__) + '/{}-new'.format(string)
	f=open(file_name, 'r')
	lister=f.readlines()
	print lister
	val={}
	#getting users
	users=[]
	for item in lister:
		if(item[0] not in users):
			users.append(item[0])
		if(item[1] not in users):
			users.append(item[1])
	val["nodes"]=[]
	val["links"]=[]
	for u in users:
		d={}
		d["id"]=u
		d["group"]=1
		val["nodes"].append(d)

	for item in lister:
		link={}
		link["source"]=item[0]
		link["target"]=item[1]
		if(item[2]==1):
			link["value"]=1
		elif(item[2]==2):
			link["value"]=10
		else:
			link["value"]=4
		val["links"].append(link)

	with open('./webapp/templates/{}.json'.format(string), 'w') as fp:
		json.dump(val, fp)


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

    #with open('Mumbai-graph', 'wb') as fp:

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
            finallist.append([density,polarity[0],polarity[1]])
        except:
            pass
    print finallist

    with open('Non-Delhi-related', 'wb') as fp:
        pickle.dump(finallist, fp)

    hashtags=[s.lower() for s in hashtags]
    hashtags=set(hashtags)
    #query=['Smog','MyRightToBreathe','CropBurning','delhipollution','delhismog','delhiairpollution','stubbleburning','SmogInDelhi','delhigaschamber','DelhiChokes','letdelhibreathe']
    query=[q.lower() for q in query]
    for q in query:
        hashtags.discard(q)
    print hashtags

    with open('Non-Delhi-related-hashtags', 'wb') as fp:
        pickle.dump(hashtags, fp)


'''
class HomePageView(TemplateView):

	def get(self,request,**kwargs):

		teimg=json.dumps(tweet_type()) #Distribution of the tweet wheather it is text or text+image

		twertw=json.dumps(tweet_retweet_distribution()) #Distribution of the tweets if its original or retweeted_status

#		popul=json.dumps(get_popularity()) #Generates the positivity,negativity and distribution of the tweets in Delhi

		favour=json.dumps(get_favcount())

		hashtags()

		return render(request,'display.html',{'text_images': teimg , 'tweet_retweet':twertw ,'favcount':favour})

# Create your views here.
'''
