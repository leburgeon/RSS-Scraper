import os

from utils.extract_utils import poll_rss_feed_for_articles
from dotenv import load_dotenv
import logging

load_dotenv()

FEED_URL = os.getenv("FEED_URL")



def main():


    # Extract all the rss articles
    articles = poll_rss_feed_for_articles(FEED_URL)
    print(f"Extracted {len(articles)} articles from the RSS feed.")
    print(articles[0].to_item_format())





if __name__ == "__main__":
    main()