# -*- coding: utf-8 -*-
import re
import sys
from time import sleep
from bs4 import BeautifulSoup
import requests
import MeCab as mc
import feedparser
from crawllist import *
import urllib
from collections import Counter
import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)
from datetime import datetime, date, timedelta
slothlib_path = 'http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/Japanese.txt'
slothlib_file = urllib.request.urlopen(slothlib_path)
slothlib_stopwords = [line.decode("utf-8").strip() for line in slothlib_file]
stop_words = [ss for ss in slothlib_stopwords if not ss==u'']
def entry_parser(feed_urls):
    #all_ent_text =""
    today_base = datetime.today()
    yesterday = (today_base - timedelta(days=1)).strftime("%Y-%m-%d")
    today = today_base.strftime("%Y-%m-%d")
    time=today_base.strftime("%H00")
    #print(yesterday)
    for feed_url in feed_urls:
         #print("feed_url is start on ",feed_url)
         feed_result = feedparser.parse(feed_url)
         ent_text =""
         enlist = [x.decode('utf-8') for x in r.zrange(feed_url+"/title/"+str(today),0,-1)]
         r.delete(feed_url+"/title/"+str(yesterday))
         for entry in feed_result.entries:

             if entry.title not in enlist:
                    ent_text+=entry.title
                    r.zadd(feed_url+"/title/"+str(today),0,str(entry.title))
             else:
                continue
         if ent_text == "":
             sleep( 2 )
             continue
         tagger = mc.Tagger('-Ochasen')
         #tagger = mc.Tagger('-Ochasen -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')
         tagger.parseToNode("")
         node = tagger.parseToNode(ent_text)
         word_list = []
         while node:
                    if node.feature.split(",")[0] in ("名詞", "動詞", "形容詞"):
                        if node.surface not in stop_words:
                            word_list.append(node.surface)
                    node = node.next
            #return word_list
         histogram = Counter(word_list) #単語わけられたあと　カウント
         #r.zincrby(feed_url+"/"+today,)
         #print(histogram)
         for key, value in histogram.most_common(): #頻出単語集計
                #print(key,value)
                r.zincrby(feed_url+"/"+str(today),str(key),int(value))   #当日URLサイトごと

                r.zincrby("all_urls/"+str(today),str(key),int(value)) #当日全URLサイト
                r.zincrby("all_urls/"+str(today)+"/"+str(time),str(key),int(value)) #当日全URLサイト1時間ごと
         #sleep(3)
         #sleep( 2 )
    return "hoge"

if __name__ == "__main__":
    args = sys.argv
    print(args)
    if len(args) != 1:
     if args[1] == "test":
       print("test")
       entry_parser(links[:5])  
     elif args[1] == "ranqmediacrawling":
       print("all")
       entry_parser(links)
     else:
       print("syntax error")
    else:
     print("nonpatch")
     entry_parser(links[:5])
      
