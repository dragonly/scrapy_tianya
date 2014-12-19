# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import scrapy
import traceback
import json
from tianya.items import TianyaPostsItem

class MongoDBPipeline(object):

    def __init__(self):

        self.conn = pymongo.Connection('localhost', 27017)
        self.db = self.conn['tianya']
        self.collections = {}
        self.collections['posts'] = self.db['posts']
        self.collections['users'] = self.db['users']

    # def _fix_sn(self, posts, offset):
    #     def _fix(post, offset):
    #         post['sn'] = post['sn'] + offset
    #         return post
    #     offsets = [offset for i in posts]
    #     posts = map(_fix, posts, offsets)
    #     return posts

    def _save_to_db(self, item, collection):
        try:
            # print repr(item['posts'])
            # _id = item['title']

            # need to set title as index
            cur = collection.find_one({'title': _id})
            if cur == None:
                collection.insert({
                    '_id'           : '0',
                    'title'         : _id,
                    'urls'          : [item['urls']],
                    'user'          : item['user'],
                    'post_time_utc' : item['post_time_utc'],
                    'click'         : item['click'],
                    'reply'         : item['reply'],
                    'posts'         : item['posts'] # this is a list of dict, not scrapy.Item
                })

            # posts exists
            else:
                posts = cur['posts']
                # posts_count = len(posts)
                # posts_to_save = item['posts']
                # posts_to_save = self._fix_sn(posts_to_save, posts_count)

                # must ensure posts contains no generated data, thus mongodb update operation
                # can filter duplicated posts already crawled
                collection.update(
                    {'_id': str(cur.count())},
                    {'$addToSet': {'posts': {'$each': item['posts']}, 'urls': item['urls']},
                    # update click & reply info
                     'click': item['click'],
                     'reply': item['reply']
                    }
                )
        except Exception, e:
            print '*'*20
            print traceback.format_exc()
            # print item['posts']
            print '*'*20
            raise e

    def process_item(self, item, spider):

        if isinstance(item, TianyaPostsItem):
            self._save_to_db(item, self.collections['posts'])

        return item

    def close_spider(self, spider):

        self.conn.disconnect()