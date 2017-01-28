#!/bin/python3.5

import asyncio
import re
from bs4 import BeautifulSoup
import requests
from aiohttp import ClientSession
import signal


class WebCrawler:

    def __init__(self, base_url='http://www.thehindu.com'):
        self.base_url = base_url
        self.MAX_LEVEL = 5
        self.MAX_LINKS = 5
        self.link_match = []
        self.current_level = 0
        self.base_url_pattern = r'\b(http[s]*://w{0,3}.{0,1}[a-zA-Z0-9-_]+.[a-zA-Z]+)'
        self.external_url_pattern = r'\b(http[s]*://w{0,3}.{0,1})'
        self.complete_url_pattern = r'\b(http[s]*://w{0,3}.{0,1}[a-zA-Z0-9-_]+.[a-zA-Z]+[/a-zA-Z0-9-_]*)'

    def shutdown(self):
        print("shutting down all tasks")
        for task in asyncio.Task.all_tasks():
            task.cancel()

    def spawn_tasks(self, links, keyword):
        tasks = []
        for link in links:
            try:
                if link.text.strip(' ') != '':
                    url_match = re.findall(
                        self.base_url_pattern, link.attrs['href'])
                    if len(url_match) and url_match[0] == self.base_url:
                        # its an full internal link
                        print("FULL_LINK: {}".format(link.attrs['href']))
                        task = asyncio.ensure_future(
                            self.crawl(link.attrs['href'], keyword))
                        tasks.append(task)
                    elif len(re.findall(self.external_url_pattern, link.attrs.get('href'))) == 0:
                        # its an internal sublink without the base_url
                        if link.attrs.get('href').find('javascript') > -1:
                            # avoid any javascript(void)
                            continue
                        url = self.base_url.rstrip('/') + link.attrs['href']
                        print("INTERNAL_LINK: {}".format(url))
                        task = asyncio.ensure_future(self.crawl(url, keyword))
                        tasks.append(task)
                    else:
                        # its an external link, could be an advertisement
                        # website. ignore it
                        continue
            except KeyError:
                print("got a key error link={}".format(link))
                # href was not found.. lets parse the link object to retrieve
                # any url
                url_match = re.findall(self.complete_url_pattern, str(link))
                if len(url_match) and url_match[0].find(self.base_url) == 0:
                    print("EXTRACTED_LINK: {}".format(url_match[0]))
                    task = asyncio.ensure_future(
                        self.crawl(url_match[0], keyword))
                    tasks.append(task)
                continue
        return tasks

    async def crawl(self, url_to_parse, keyword='tiruchirapalli'):
        if len(self.link_match) >= self.MAX_LINKS:
            self.shutdown()
        if self.current_level >= self.MAX_LEVEL:
            print(
                "max level reached current_level={}".format(
                    self.current_level))
            self.shutdown()

        async with ClientSession() as session:
            async with session.get(url_to_parse) as response:
                content = await response.text()
                bs_content = BeautifulSoup(content, 'html.parser')

        # first find if any of the links in the current page have the keyword
        links = bs_content.find_all('a')
        for link in links:
            if link.text.lower().find(keyword.lower()) > 0:
                with open('links.txt', 'w+') as file:
                    file.write("match={}".format(link.text))
                    file.write("link={}".format(link.attrs['href']))
                print("match={}".format(link.text))
                print("link={}".format(link.attrs['href']))
                self.link_match.append(link)

        # or current_level < MAX_LEVEL:
        if len(self.link_match) < self.MAX_LINKS:
            self.current_level += 1
            # find the sublinks of this base_url from links and call crawls
            # asynchronously on them
            tasks = self.spawn_tasks(links, keyword)
            results = asyncio.gather(*tasks)
        else:
            self.shutdown()


if __name__ == '__main__':
    URL = "http://www.thehindu.com"
    KEYWORD = 'chennai'
    loop = asyncio.get_event_loop()
    crawlObj = WebCrawler(base_url=URL)
    loop.add_signal_handler(signal.SIGINT, crawlObj.shutdown)
    future = asyncio.ensure_future(crawlObj.crawl(URL, KEYWORD))
    loop.run_until_complete(future)
