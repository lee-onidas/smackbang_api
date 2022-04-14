from textblob import TextBlob
import tweepy
import matplotlib.pyplot as plt
import pandas as pd
import os
from dotenv import load_dotenv, find_dotenv
import re
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from smackbang.matches import get_matches

env_path = find_dotenv()
load_dotenv(env_path)
TWITTER_CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

consumerKey = TWITTER_CONSUMER_KEY
consumerSecret = TWITTER_CONSUMER_SECRET
accessToken = TWITTER_ACCESS_TOKEN
accessTokenSecret = TWITTER_ACCESS_TOKEN_SECRET
auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)
api = tweepy.API(auth)

#Sample DataFrame please edit!
#matches_df = get_matches(origin_one='LHR', origin_two='CDG', departure_date='01/12/2022', continent='EU', return_date='', currency='USD')

#List of sample cities from matches_df
#city_list = matches_df.index.values

#Sentiment Analysis

def analyze_tweet(cities):
    noOfTweet = 200
    list_df= []
    for city in cities:

        #tweets = tweepy.Cursor(api.search_tweets(), q=keyword).items(noOfTweet)
        tweets = api.search_tweets(q=city, count=noOfTweet)

        tweet_list = []

        for tweet in tweets:
            tweet_list.append(tweet.text)

        #Tweets to DF
        tweet_list = pd.DataFrame(tweet_list)

        #Clean the data
        tweet_list.drop_duplicates(inplace = True)
        tw_list = pd.DataFrame(tweet_list)

        #Make another column to compare
        tw_list["text"] = tw_list[0]

        #More cleaning
        remove_rt = lambda x: re.sub('RT @\w+:'," ",x)
        rt = lambda x: re.sub('(@[A-Za-z0–9]+)|(\w+:\/\/\S+)'," ",x)
        removen = lambda x: re.sub('\n',' ', x)
        tw_list["text"] = tw_list.text.map(remove_rt).map(rt).map(removen)
        tw_list["text"] = tw_list.text.str.lower()

        #I will try to simplify this
        tw_list[["polarity", "subjectivity"]] = tw_list["text"].apply(lambda Text: pd.Series(TextBlob(Text).sentiment))
        for index, row in tw_list["text"].iteritems():
            score = SentimentIntensityAnalyzer().polarity_scores(row)
            neg = score["neg"]
            neu = score["neu"]
            pos = score["pos"]
            comp = score["compound"]
            if neg > pos:
                tw_list.loc[index, "sentiment"] = "negative"
            elif pos > neg:
                tw_list.loc[index, "sentiment"] = "positive"
            else:
                tw_list.loc[index, "sentiment"] = "neutral"
                tw_list.loc[index, "neg"] = neg
                tw_list.loc[index, "neu"] = neu
                tw_list.loc[index, "pos"] = pos
                tw_list.loc[index, "compound"] = comp

        def thumb(neg,neu,pos):
            if pos+(neu/2) >= neg+(neu/2):
                return "👍"
            else:
                return "👎"

        #Output a simplified DF
        def count_values_in_column(data,feature):
            new_df = pd.DataFrame({"Score":["neutral","positive","negative"],"Total":[0,0,0], "Percentage":[0,0,0]})
            new_df.set_index("Score",inplace =True)
            new_df["Total"] = data.loc[:,feature].value_counts(dropna=False)
            new_df["Percentage"]=round(data.loc[:,feature].value_counts(dropna=False,normalize=True)*100,2)
            new_df = new_df.fillna(0)
            new_df["City"] = city
            new_df["Verdict"] = thumb(new_df["Total"].loc["negative"],
                                      new_df["Total"].loc["neutral"],
                                      new_df["Total"].loc["positive"])
            list_df.append(new_df)


        #Count_values for sentiment
        count_values_in_column(tw_list,"sentiment")
    result =  pd.concat(list_df)
    return result.reset_index(drop=True).drop(columns=["Total","Percentage"]).drop_duplicates()


if __name__ == '__main__':
    print(analyze_tweet(["Bangkok"]))
