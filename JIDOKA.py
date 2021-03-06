import os
import sys
import re
import pandas as pd
import graphnetworks as gn
import datetime
import argparse
import cleandata as cd

def scrapTweets(query, limit=None, lang='', output='tweets.csv', begin = datetime.date.today()-datetime.timedelta(days=60), end = datetime.date.today()):
    from twitterscraper import query_tweets;

    data = []
    for tweet in query_tweets(query, limit=limit, lang=lang, begindate=begin, enddate=end):
        data.append([tweet.tweet_id,tweet.text])
    
    tweets = pd.DataFrame(data, columns=['id','Tweet'])
    tweets = tweets.drop_duplicates()
    tweets = tweets.dropna()
    tweets.to_csv(output, index=False)
    return

def getSubsetsHT(df, label):
    subsets = []
    for i, row in df.iterrows():
        text = row[label]
        ht = cd.getHashtags(text)
        if ht:
            ht = [i.lower() for i in ht]
            subsets.append(ht)
    return subsets    

def saveConjuntos(path,filename, data):
    makeDirectory(path)

    with open(path+filename, 'w') as f:
        for item in data:
            f.write(', '.join(map(str, item)))
            f.write('\n')
        f.close()

def makeDirectory(path):
    os.makedirs(path, exist_ok=True)

def readData(filename):
    tweets = pd.read_csv(filename)
    tweets = tweets.dropna()
    return tweets    

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JIDOKA")
    
    #Descargar
    parser.add_argument('--topic', default=None, type=str, help='topic name for the project.')
    
    parser.add_argument('--query', default=None, type=str, help='query to scrap tweets.')
    parser.add_argument('--limit', default=500, type=int, help='set a limit number for scrap tweets.')
    parser.add_argument('--lang', default='', type=str, help='set language for the query')
        
    #explorar

    parser.add_argument('--sets', default=None, type=str, help='input .txt with hashtags subsets')
    parser.add_argument('--nt', default=1, type=int, help='set min node threshold for of network')
    parser.add_argument('--et', default=1, type=int, help='set min edge threshold of network')
    parser.add_argument('--iso', default=False, type=bool, help='remove isolate nodes')
    parser.add_argument('--comm', default=False, type=bool, help='if True compute communities in network')
    parser.add_argument('--vis', default=False, type=bool, help='if True show graph of hashtags')

    
    args = parser.parse_args()
           
    if args.topic:
        topic = args.topic
    else:
        topic = 'DATA'
    
    path = os.getcwd()+'/'+topic
    makeDirectory(path)
    
    if args.query:
        filename = path+'/'+topic+'.csv'
        
        scrapTweets(args.query, limit=args.limit, lang=args.lang, output=filename)
        
        tweets = readData(filename)

        hts = getSubsetsHT(tweets,'Tweet')

        saveConjuntos(path+'/',topic+'_subsets.txt', hts)

        subsetfile = path+'/'+topic+'_subsets.txt'
                    
        network = gn.HashtagsData(subsetfile, args.nt,  args.et, args.iso)
    
    elif args.sets:
        network = gn.HashtagsData(args.sets, args.nt,  args.et, args.iso)
                
    if args.comm:
        network.getCommunity()
        
    if args.vis:
        network.showGraph()

    network.data.to_csv(network._path[0]+'network_data_N'+str(args.nt)+'E'+str(args.et)+'.csv')

    
