#-*- coding: utf-8 -*-
'''
Created on 2015/10/26 by Michael Findlater
NewsDog
'''
import praw
import codecs
import string
from ftfy import fix_text
from newspaper import Article

# Configuration
SUBREDDIT = 'worldnews'
GEOSOURCE_COUNTRY = 'geodata/GEODATASOURCE-COUNTRY.TXT'
DEMS = 'geodata/demonyms.txt'
        
class NewsDog():
    geohits = [] # (country, count)
    def __init__(self):
        '''Establishes a connection to Reddit'''
        self.reddit = praw.Reddit(user_agent='NewsDog')
        
    def add_geohit(self, place):
        # If exists, increment
        results = [n for n in self.geohits if n[0] == place]
        if results:
            self.geohits[self.geohits.index(results[0])][1] += 1
        # If not, create
        else:
            self.geohits.append([place, 1])
            
    def analyze_day(self, limit=5):
        submissions = self.reddit.get_subreddit(SUBREDDIT).get_top_from_year(limit=limit)
        for post in submissions:
            print(post)
            print(post.url)
            if 'www.reddit.com' not in post.url:
                self.get_article(post.url)
            
    def geo_sources(self, text):
        # Remove punctuation
        remove_punct_map = dict.fromkeys(map(ord, string.punctuation))
        text = text.replace('\n', ' ').translate(remove_punct_map)
        country_data = []
        
        country_file = codecs.open(GEOSOURCE_COUNTRY, 'r', encoding='utf-8')
        for line in country_file.read().split('\n'):
            line_split = line.split('\t')
            if len(line_split)-1 == 3 and 'COUNTRY_NAME' not in line:
                country_data.append( (line_split[0], line_split[1], line_split[2], line_split[3].strip('\r')) )
        country_file.close()
        text_split = text.split(' ')
        
        # Find countries mentioned
        for word in text_split:
            for row in country_data:
                if row[3] in word:
                    self.check_country(word)
                elif text_split.index(word)+1 <= len(text_split)-1 and word+' '+text_split[text_split.index(word)+1] == row[3]:
                    print('Direct match', word+' '+text_split[text_split.index(word)+1], 'and', row[3])
                    self.check_country(word+' '+text_split[text_split.index(word)+1])
    
    def get_article(self, url):
        article = Article(url)
        article.download()
        article.parse()
        self.geo_sources(fix_text(article.text))
    
    def geo_csv(self):
        for item in self.geohits:
            print(item[0]+', '+str(item[1]))
            
    def check_country(self, name):
        name = name.lower()
        end = False
        c_defs = codecs.open(DEMS, 'r', encoding='utf-8')
        while not end:
            # Separate lines
            for line in c_defs.read().split('\n'):
                # Separate elements
                for element in line.split(','):
                    if name == element.lower():
                        # Add a match, and exit while loop
                        self.add_geohit(line.split(',')[0])
                        end = True # Found so exit
            end = True
        c_defs.close()

def main():
    nd = NewsDog()
    nd.analyze_day(limit=100)
    nd.geo_csv()

if __name__ == '__main__': main()