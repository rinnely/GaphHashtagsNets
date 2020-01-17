graph networks

A tool for visualize networks depending on their weights

Installing dependencies
  For linux users:
    1. Install python

    run the following commands in a terminal
    2. Install Bokeh: pip install bokeh

    3 Install networks: pip install networkx

Usage
python graphNetworks-v3.py --help
usage: graphNetworks-v3.py [-h] [--sets SETS] [--frq FRQ] [--mw MW]

Graphs

optional arguments:
  -h, --help   show this help message and exit
  --sets SETS  input sets of hastags
  --frq FRQ    input min freq a hashtag appears
  --mw MW      input min weight of the network

Running
run graph-networks and wirite the file that contains the subsets of hashtags file. frequency and weight parameters are optional

python graphNetworks-v3.py --sets ./proyecto/sets_aborto_500.txt --frq 2

python graphNetworks-v3.py --sets ./mohammad/set_Atheism_ns.txt --frq 2 --mw 2

this will generate an interactive html file with the network result that can be open on any browser
