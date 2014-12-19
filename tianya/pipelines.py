# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import scrapy
import traceback
import json
from tianya.items import TianyaPostsItem, TianyaUserItem

class MongoDBPipeline(object):

    def __init__(self):

        self.conn = pymongo.Connection('localhost', 27017)
        self.db = self.conn['tianya']
        self.collections = {}
        self.collections['posts'] = self.db['posts']
        self.collections['users'] = self.db['users']

    def _save_to_db(self, item, collection):
        try:
            if isinstance(item, TianyaPostsItem):
                # need to set title as index
                cur = collection.find_one({'title': item['title']})
                if cur == None:
                    collection.insert({
                        '_id'           : str(collection.count()),
                        'title'         : item['title'],
                        'urls'          : [item['urls']],
                        'user'          : item['user'],
                        'post_time_utc' : item['post_time_utc'],
                        'click'         : item['click'],
                        'reply'         : item['reply'],
                        'posts'         : item['posts'] # this is a list of dict, not scrapy.Item
                    })

                # posts exists
                else:
                    # must ensure posts contains no generated data, thus mongodb update operation
                    # can filter duplicated posts already crawled
                    if item['urls'] in cur['urls']:
                        collection.update(
                            {'title': item['title']},
                            {'$set': {
                                'click': item['click'],
                                'reply': item['reply']
                            }}
                        )
                    else:
                        collection.update(
                            {'title': item['title']},
                            {'$addToSet': {'posts': {'$each': item['posts']}, 'urls': item['urls']},
                            # update click & reply info
                             '$set': {
                                'click': item['click'],
                                'reply': item['reply']
                             }
                            }
                        )
            elif isinstance(item, TianyaUserItem):
                collection.insert({
                    '_id': item['uid'],
                    'uname': item['uname']
                })
        except Exception, e:
            print '*'*20
            print traceback.format_exc()
            print '*'*20
            raise e

    def process_item(self, item, spider):

        if isinstance(item, TianyaPostsItem):
            item['urls'] = item['urls'].split('?')[0]
            self._save_to_db(item, self.collections['posts'])
        elif isinstance(item, TianyaUserItem):
            self._save_to_db(item, self.collections['users'])

        return item

    def close_spider(self, spider):

        self.conn.disconnect()
