scrapy_tianya
=============

A crawler for bbs.tianya.cn, using scrapy as crawler framework

### Prerequisite:
- scrapy
- mongodb
- pymongo

PS: Actually you can rewrite tianya/pipelines.py to change the storage backend, instead of mongodb :)

PPS: xpath links are easy to get in Chrome Developer Tool

### Instruction
```bash
cd path/to/repo
mkdir job
scrapy crawl tianyaSpider -s JOBDIR=/path/to/job/job-1_or_whatever
```
