"""This script will be used to define the metrics for the newsletter report,

These will accquired by connecting to dynamoDB and running queries to get the relevant data for the newsletter report.

1)Mention Volume:

count(distinct article_id) where entity_id = X

2)Sentiment Distribution:
For each company in date range:

(pos/neu/neg mention)/articles

3)Share of Voice:
For each company in date range:

SOV= company article count/total article count
"""
