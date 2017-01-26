#!/bin/python3.5
import re
from bs4 import BeautifulSoup
import requests

def crawl(base_url, keyword):
  html_page = requests.get(base_url)
  bs_content = BeautifulSoup(html_page.content, 'html.parser')
  link_match = []
  # first find if any of the links in the current page have the keyword
  links = bs_content.find_all('a')
  for link in links:
    if link.text.find(keyword) > 0:
      link_match.push(link)

  #if there are no matches to the link in the current page then
  #we will spawn series of async calls to crawl() in the current page
  # that will go and fetch pages for sublinks
  if not len(link_match):
    #find the sublinks of this base_url from links and call crawls asynchronously on them