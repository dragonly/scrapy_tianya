# -*- coding: utf-8 -*-
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from tianya.items import TianyaPostItem, TianyaPostsItem

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

    rules = (
        Rule(LinkExtractor(allow=r'/post.*\.shtml'), callback='parse_post'),
        Rule(LinkExtractor(allow=r'/list.*\.shtml'), callback='parse_list'),
    )

    def parse_list(self, response):

        time.sleep(random.random())

        self.log('Parsing list page %s|%s'
            % (string.strip(response.meta.get('link_text', '')), response.url))

    def _parse_time(self, time_str):
        try:
            date, time = time_str.split(' ')
            args = date.split('-')
            args.extend(time.split(':'))
            args = [int(i) for i in args]
            utc_timestamp = (datetime(*args) - datetime(1970, 1, 1)).total_seconds()
            # self.log('utc_timestamp: %s' % int(utc_timestamp))
            return int(utc_timestamp)
        except Exception, e:
            print 'time_str: %s' % repr(time_str)
            raise e

    def parse_post(self, response):

        time.sleep(random.random())

        self.log('Parsing post page %s|%s'
            % (string.strip(response.meta.get('link_text', '')), response.url))

        # from scrapy.shell import inspect_response
        # inspect_response(response)

        sel = Selector(response)
        posts = TianyaPostsItem()

        posts['urls'] = response.url
        posts['title'] = ''.join(sel.xpath('//*[@id="post_head"]/h1/span[1]/span/text()').extract())
        posts['post_time_utc'] = string.strip(''.join(sel.xpath('//*[@id="post_head"]/div[1]/div[2]/span[2]/text()').extract()).split(unicode('：'))[-1])
        posts['post_time_utc'] = self._parse_time(posts['post_time_utc'])
        posts['click'] = int(string.strip(''.join(sel.xpath('//*[@id="post_head"]/div[1]/div[2]/span[3]/text()').extract()).split(unicode('：'))[-1]))
        posts['reply'] = int(string.strip(''.join(sel.xpath('//*[@id="post_head"]/div[1]/div[2]/span[4]/text()').extract()).split(unicode('：'))[-1]))
        x = sel.xpath('//*[@id="post_head"]/div[1]/div[2]/span[1]/a')
        user = {}
        user['uid'] = int(''.join(x.xpath('@uid').extract()))
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
                post['sn'] = i
                post['content'] = ''.join(sel_i.xpath('.//*[contains(@class, "bbs-content")]/text()').extract()).replace('\t', '')

                post['post_time_utc'] = string.strip(''.join(sel_i.xpath('.//*[@class="atl-info"]/span[2]/text()').extract()).split(unicode('：'))[-1])
                if post['post_time_utc'] != '':
                    post['post_time_utc'] = self._parse_time(post['post_time_utc'])
                else:
                    post['post_time_utc'] = posts['post_time_utc']
                user = {}
                user['uid'] = int(''.join(sel_i.xpath('.//*[@class="atl-info"]/span[1]/a/@uid').extract()))
                user['uname'] = ''.join(sel_i.xpath('.//*[@class="atl-info"]/span[1]/a/@uname').extract())
                post['user'] = user
            except Exception, e:
                # self.log('Exception while parsing posts\n%s\n%s' % (e, traceback.format_exc()))
                user = {
                    'uid': posts['user']['uid'],
                    'uname': posts['user']['uname']
                }
                post['user'] = user
                print traceback.format_exc()
                print 'post: %s' % post
            finally:
                posts['posts'].append(post)
            # self.log(json.dumps(dict(post), ensure_ascii=False))
            # from scrapy.shell import inspect_response
            # inspect_response(response)

        return posts

