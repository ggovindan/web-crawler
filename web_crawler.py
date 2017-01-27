#!/bin/python3.5

import asyncio
import re
from bs4 import BeautifulSoup
import requests

base_url = 'http://www.bbc.com'
MAX_LEVEL = 5
MAX_LINKS = 1
current_level = 0
link_match = []
base_url_pattern = r'\b(http[s]*://w{0,3}.{0,1}[a-zA-Z0-9-_]+.[a-zA-Z]+)'
external_url_pattern = r'\b(http[s]*://w{0,3}.{0,1})'

def shutdown():
  print("shutting down all tasks")
  for task in asyncio.Task.all_tasks():
    task.cancel()

async def crawl(url_to_parse, keyword):
  if len(link_match) >= MAX_LINKS:
    shutdown()
  html_page = requests.get(url_to_parse)
  bs_content = BeautifulSoup(html_page.content, 'html.parser')
  tasks = []
  
  # first find if any of the links in the current page have the keyword
  links = bs_content.find_all('a')
  for link in links:
    if link.text.lower().find(keyword.lower()) > 0:
      print("match={}".format(link.text))
      print("link={}".format(link.attrs['href']))
      link_match.append(link)

  if len(link_match) < 5: #or current_level < MAX_LEVEL:
    #find the sublinks of this base_url from links and call crawls asynchronously on them
    for link in links:
      if link.text.strip(' ') != '':
        if len(re.findall(base_url_pattern, link.attrs.get('href'))): 
          #its an full internal link
          print("FULL_LINK: {}".format(link.attrs['href']))
          task = asyncio.ensure_future(crawl(link.attrs['href'], keyword))
          tasks.append(task)
        elif len(re.findall(external_url_pattern, link.attrs.get('href'))) == 0:
          #its an internal sublink without the base_url
          if link.attrs.get('href').find('javascript') > -1:
            continue
          url = base_url.rstrip('/') + link.attrs['href']
          print("INTERNAL_LINK: {}".format(url))
          task = asyncio.ensure_future(crawl(url, keyword))
          tasks.append(task)
        else:
          #its an external link, could be an advertisement website. ignore it
          continue
    results = asyncio.gather(*tasks)
  else:
    shutdown()

loop = asyncio.get_event_loop()
future = asyncio.ensure_future(crawl(base_url, 'Kashmir'))
loop.run_until_complete(future)


# [^.]* flung [^.]*\.