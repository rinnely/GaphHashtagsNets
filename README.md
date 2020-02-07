JIDOKA

A tool for visualize networks depending on their weights

Installing dependencies

for linux users:
  
    	1. Install python
    	
	2. Download de latest release of chromedriver https://chromedriver.storage.googleapis.com/index.html?path=79.0.3945.36/
    	
	3. Install twitter-scraper from https://github.com/bisguzar/twitter-scraper

    	run the following commands in a terminal
    	
		4. Install Bokeh: pip install bokeh
    		
		5 Install networks: pip install networkx

Usage

    python JIDOKA.py --help
    usage: JIDOKA.py [-h] [--topic TOPIC] [--query QUERY] [--limit LIMIT]
                 [--lang LANG] [--sets SETS] [--nt NT] [--et ET]

JIDOKA
   
   optional arguments:
  
    -h, --help     show this help message and exit
    --topic TOPIC  topic name for the project.
    --query QUERY  query to scrap tweets.
    --limit LIMIT  set a limit number for scrap tweets.
    --lang LANG    set language for the query
    --sets SETS    input .txt with hashtags subsets
    --nt NT        set min node threshold for the graph
    --et ET        set min edge threshold for the graph
    --byO BYO      get Matrix by 1 over n-1 elements in subsets
    --dnt DNT      set min threshoold for remove disconected nodes



Running

run JIDOKA and wirite the topic name of the project, a query to scrape tweets. Topic, lang, nt, et are optional. The query can be a word like "aborto" or many hashtags like "#aborto OR #seraley OR #sialavida", always with quotes.

    python JIDOKA.py --topic aborto --query "#aborto OR #seraley OR #sialavida" --lang es
    
this will scrape tweets using the query and generate a graph of the hashtags used in tweets.

if you already have the subsets of hashtags you cant explore them. 

run JIDOKA and wirite the file that contains the subsets of hashtags. nt and et parameters are optional
 
    python JIDOKA.py --sets ./proyecto/sets_culiacan.txt  --nt 2 --et 1

this will generate the graph of the hashtags.
