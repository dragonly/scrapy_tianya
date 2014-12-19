# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field

class TianyaPostItem(Item):
    # sn              = Field()
    user            = Field()
    post_time_utc   = Field()
    content         = Field()
    # comments        = Field()

class TianyaPostsItem(Item):
    urls            = Field()
    title           = Field()
    user            = Field()
    post_time_utc   = Field()
    click           = Field()
    reply           = Field()
    posts           = Field()

class TianyaUser(Item):
    uid             = Field()
    uname           = Field()