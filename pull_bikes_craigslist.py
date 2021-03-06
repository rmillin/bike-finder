#!/usr/bin/env python

from bs4 import BeautifulSoup
import urllib3, urllib
import requests
import certifi
import numpy as np
import argparse
import time
import os
from collections import defaultdict
import numpy as np

def get_craigslist_postings(city,slp_min = 10, slp_max = 30):
 
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())

    # Get URLs for Craigslist postings
    posting_URLs = []
    url = "http://"+city+".craigslist.org/d/bicycles/search/bia" #main page
    response = http.request('GET', url)
    soup = BeautifulSoup(response.data, "lxml")
    items = soup('p')
    for item in items[:-1]:
        posting_URLs.append(item('a')[0]['href'])

    satisfied = False
    n = 1
    while not(satisfied) and n < 50:
        time.sleep(np.random.randint(slp_min,slp_max) + np.random.rand())
        url = "https://"+city+".craigslist.org/search/bia?s="+str(n*120) #additional pages
        print(url)
        response = http.request('GET', url)
        soup = BeautifulSoup(response.data, "lxml")
        items = soup('p')
    
        if len(items) > 1:  
            for item in items[:-1]:
                 posting_URLs.append(item('a')[0]['href'])
        else:
            satisfied = True
        n += 1

    print("Found",len(posting_URLs),"Craigslist postings")
    
    return posting_URLs


def check_against_saved_postings(posting_URLs, city):

    # Open csv file 
    if os.path.exists('data/'+city+'_craigslist_postings.csv'):
        fid = open('data/'+city+'_craigslist_postings.csv','r')
        lines = fid.readlines()
    
        # Get saved URLs
        saved_posting_URLs = []
        for line in lines[1:]:
            saved_posting_URLs.append(line.split(',')[2].replace(' ',''))
        fid.close()
 
        # Find postings that haven't been saved in the directory already
        new_posting_URLs = []   
        for URL in posting_URLs:
            if not(URL in saved_posting_URLs):
                new_posting_URLs.append(URL)  
            
        # Find postings that have been deleted from Craigslist      
        deleted_posting_URLs = []
        for URL in saved_posting_URLs:
            if not(URL in posting_URLs):
                deleted_posting_URLs.append(URL)
    else:
      new_posting_URLs = posting_URLs
      deleted_posting_URLs = []

    return new_posting_URLs, deleted_posting_URLs


def get_new_posting_attrs(posting_URLs, city, slp_min = 60, slp_max = 90):
    
    # Pull data from posting_URLs
    n_items = len(posting_URLs)
    
    bike_attrs = defaultdict(list)
    for var in ['title','price','URL','imageURL','imagefile','description',\
                'timeposted','latitude','longitude','biketype']:
        bike_attrs[var] = []
    
    if not(os.path.exists('data/'+city+'_craigslist_postings.csv')):
        fid = open('data/'+city+'_craigslist_postings.csv','w')
        for key in bike_attrs.keys():
            fid.write(key+',')
        fid.write('\n')
        fid.close()   

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())

    # Get unique counter for saving images in dir 'data'
    j = 0
    files = os.listdir('data')
    for name in files:
        if name.endswith('.jpg') and name.startswith(city):
            if int(name[-9:-4]) >= j:
                j = int(name[-9:-4]) + 1
    print("Starting at image",j)

    fid = open('data/'+city+'_craigslist_postings.csv','a')
    for i in range(20):#n_items):
        print("Posting",i,"of",n_items)
        time.sleep(np.random.randint(slp_min,slp_max) + np.random.rand())
        response = http.request('GET',posting_URLs[i])
        soup = BeautifulSoup(response.data, "lxml")
        images = soup('img')
        
        # Save first image and its URL. It takes too much time to process all images
        # for a bike.
        if len(images) > 0:
            imageURL = images[0]['src'] 
            imagefile = city+'_craigslist_image'+'{0:05d}'.format(j)+'.jpg'
            urllib.request.urlretrieve(imageURL, 'data/'+imagefile)
            j += 1
        
            time.sleep(np.random.randint(slp_min,slp_max) + np.random.rand())
            bike_attrs['title'].append(soup.find('span',{'id':'titletextonly'}).text.strip().replace(',',' '))
            bike_attrs['price'].append(soup.find('span',{'class':'price'}).text.strip()[1:])
            bike_attrs['description'].append(soup.find('section',{'id':'postingbody'}).text.strip().replace('\n',' ').replace(',',' '))
            bike_attrs['imageURL'].append(imageURL)
            bike_attrs['imagefile'].append(imagefile)
            bike_attrs['URL'].append(posting_URLs[i])
            bike_attrs['timeposted'].append(soup.find('p',{'class':'postinginfo reveal'}).text.strip()[-18:])

            lat, long = get_lat_long(str(soup.find('div',{'viewposting'})))
            bike_attrs['latitude'].append(lat)
            bike_attrs['longitude'].append(long)
            
            bike_attrs['biketype'].append('')

            for key in bike_attrs.keys():
                fid.write(bike_attrs[key][-1]+', ')
            fid.write('\n')
                    
    fid.close()
         
    return bike_attrs


def get_lat_long(loc_string):
    
    p = loc_string.split()
    
    if len(p) > 1:
        lat = p[3][15:-1]
        long = p[4][17:-1]
    else:
        lat = ''
        long = ''

    return lat,long


def remove_attrs(old_postings, city):

    return old_postings

parser = argparse.ArgumentParser(
    description="Find craigslist bike postings", parents=())
parser.add_argument("-c", "--city", default='seattle',
    help='Search city')
     
args, extra_args = parser.parse_known_args()

posting_URLs = get_craigslist_postings(args.city)

new_posting_URLs, deleted_posting_URLs = check_against_saved_postings(posting_URLs, args.city)

bike_attrs = get_new_posting_attrs(new_posting_URLs, args.city)