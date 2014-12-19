# -*- coding: utf-8 -*-
from scrapy import log
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.selector import Selector
from tianya.items import TianyaUserItem, TianyaPostsItem

import random
import time
import string
import json
import sys
import traceback
import copy
from datetime import datetime

reload(sys)
sys.setdefaultencoding('utf8')

class TianyaspiderSpider(CrawlSpider):
    name = "tianyaSpider"
    allowed_domains = ["tianya.cn"]
    start_urls = (
        'http://bbs.tianya.cn/',
    )

    posts_link_extractor = LinkExtractor(allow=r'/post.*\.shtml')
    lists_link_extractor = LinkExtractor(allow=r'/list.*\.shtml')

    rules = (
        Rule(posts_link_extractor, callback='parse_post'),
        Rule(lists_link_extractor, callback='parse_list'),
    )

    def _parse_time(self, time_str):
        try:
            date, time = time_str.split(' ')
            args = date.split('-')
            args.extend(time.split(':'))
            args = [int(i) for i in args]
            utc_timestamp = (datetime(*args) - datetime(1970, 1, 1)).total_seconds()
            # self.log('utc_timestamp: %s' % int(utc_timestamp))
            return utc_timestamp
        except Exception, e:
            print 'time_str: %s' % repr(time_str)
            raise e

    def _extract_links_generator(self, response):
        lists_links = [l for l in self.lists_link_extractor.extract_links(response)]
        for link in lists_links:
            yield Request(url=link.url, callback=self.parse_list)

        posts_links = [l for l in self.posts_link_extractor.extract_links(response)]
        for link in posts_links:
            yield Request(url=link.url, callback=self.parse_post)

        self.log('Extracting links:\nlists_links: %s\nposts_links: %s' % (lists_links, posts_links), level=log.INFO)

    def parse_list(self, response):

        time.sleep(random.random())

        self.log('Parsing list page %s|%s'
            % (string.strip(response.meta.get('link_text', '')), response.url), level=log.INFO)

        for link in self._extract_links_generator(response):
            yield link

    def parse_post(self, response):

        time.sleep(random.random())

        self.log('Parsing post page %s|%s'
            % (string.strip(response.meta.get('link_text', '')), response.url), level=log.INFO)

        # from scrapy.shell import inspect_response
        # inspect_response(response)

        sel = Selector(response)
        posts = TianyaPostsItem()

        posts['urls'] = response.url
        posts['title'] = ''.join(sel.xpath('//*[@id="post_head"]/h1/span[1]/span/text()').extract())
        posts['post_time_utc'] = string.strip(''.join(sel.xpath('//*[@id="post_head"]/div[1]/div[2]/span[2]/text()').extract()).split(unicode('：'))[-1])
        posts['post_time_utc'] = self._parse_time(posts['post_time_utc'])
        posts['click'] = string.strip(''.join(sel.xpath('//*[@id="post_head"]/div[1]/div[2]/span[3]/text()').extract()).split(unicode('：'))[-1])
        posts['reply'] = string.strip(''.join(sel.xpath('//*[@id="post_head"]/div[1]/div[2]/span[4]/text()').extract()).split(unicode('：'))[-1])
        x = sel.xpath('//*[@id="post_head"]/div[1]/div[2]/span[1]/a')
        user = {}
        user['uid'] = ''.join(x.xpath('@uid').extract())
        user['uname'] = ''.join(x.xpath('@uname').extract())
        posts['user'] = user
        posts['posts'] = []

        sel_posts = sel.xpath('//*[contains(@class, "atl-main")]/*[contains(@class, "atl-item")]')
        for i, sel_i in enumerate(sel_posts):
            try:
                # use TIanyaPostItem will cause pymongo to raise InvalidDocument Exception
                # because it inherits from scrapy.Item, which is a customed class, thus
                # cannot be bson encoded
                post = {} # TianyaPostItem()
                post['content'] = ''.join(sel_i.xpath('.//*[contains(@class, "bbs-content")]/text()').extract()).replace('\t', '')

                post['post_time_utc'] = string.strip(''.join(sel_i.xpath('.//*[@class="atl-info"]/span[2]/text()').extract()).split(unicode('：'))[-1])
                if post['post_time_utc'] != '':
                    post['post_time_utc'] = self._parse_time(post['post_time_utc'])
                else:
                    post['post_time_utc'] = posts['post_time_utc']
                user = {}
                user['uid'] = ''.join(sel_i.xpath('.//*[@class="atl-info"]/span[1]/a/@uid').extract())
                user['uname'] = ''.join(sel_i.xpath('.//*[@class="atl-info"]/span[1]/a/@uname').extract())
                if user['uid'] == '' or user['uname'] == '':
                    raise Exception('No user info extracted!')
                post['user'] = user
            except Exception, e:
                self.log('Exception while parsing posts\n%s\n%s' % (e, traceback.format_exc()))
                post['user'] = posts['user']
                # print traceback.format_exc()
            finally:
                posts['posts'].append(post)
                self.log(json.dumps(post, ensure_ascii=False), level=log.INFO)
            # from scrapy.shell import inspect_response
            # inspect_response(response)

        yield posts

        for post in posts['posts']:
            userItem = TianyaUserItem()
            userItem['uid'] = post['user']['uid']
            userItem['uname'] = post['user']['uname']
            yield userItem

        for link in self._extract_links_generator(response):
            yield link


