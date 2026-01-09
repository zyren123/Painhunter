"""RSS Fetcher module for Reddit pain point discovery."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict
import feedparser
import httpx


# Reddit RSS endpoint
REDDIT_RSS_BASE = "https://www.reddit.com/r/{subreddit}/top/.rss?t=day"

# User-Agent to mimic browser and avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def parse_reddit_timestamp(published: str) -> datetime:
    """Parse Reddit's feed timestamp format."""
    # Reddit uses RFC 2822 format
    parsed = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S%z")
    return parsed


def is_within_hours(published_dt: datetime, hours: int = 24) -> bool:
    """Check if the post was published within the specified hours."""
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=hours)
    return published_dt >= threshold


def fetch_subreddit_posts(subreddit: str, hours_ago: int = 24, max_posts: int = 100) -> List[Dict]:
    """Fetch posts from a subreddit's RSS feed within the specified time window.

    Args:
        subreddit: Subreddit name (without 'r/')
        hours_ago: Only fetch posts from the last N hours
        max_posts: Maximum number of posts to fetch (default 100)

    Returns:
        List of post dictionaries
    """
    url = REDDIT_RSS_BASE.format(subreddit=subreddit)
    posts = []

    with httpx.Client(headers=HEADERS, timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        for entry in feed.entries:
            if len(posts) >= max_posts:
                break
            try:
                # Parse publication time
                if hasattr(entry, 'published'):
                    published_dt = parse_reddit_timestamp(entry.published)
                elif hasattr(entry, 'updated'):
                    published_dt = parse_reddit_timestamp(entry.updated)
                else:
                    continue

                # Skip if outside time window
                if not is_within_hours(published_dt, hours_ago):
                    continue

                post = {
                    "subreddit": subreddit,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": published_dt.isoformat(),
                    "author": entry.get("author", ""),
                    "summary": entry.get("summary", "")[:500],  # Truncate long summaries
                }
                posts.append(post)
            except Exception as e:
                print(f"Error parsing entry: {e}")
                continue

    return posts


def fetch_reddit_posts(
    subreddits: List[str] = None,
    hours_ago: int = 24,
    max_posts_per_subreddit: int = 100,
) -> List[Dict]:
    """Main function to fetch Reddit posts.

    Args:
        subreddits: List of subreddit names (without 'r/')
        hours_ago: Only fetch posts from the last N hours
        max_posts_per_subreddit: Maximum posts per subreddit (default 100)

    Returns:
        List of post dictionaries (unfiltered)
    """
    if subreddits is None:
        subreddits = ["SaaS", "Entrepreneur"]

    all_posts = []
    for subreddit in subreddits:
        print(f"Fetching posts from r/{subreddit}...")
        posts = fetch_subreddit_posts(subreddit, hours_ago, max_posts_per_subreddit)
        print(f"  Found {len(posts)} posts in the last {hours_ago} hours")
        all_posts.extend(posts)

    print(f"\nTotal posts fetched: {len(all_posts)}")

    return all_posts


if __name__ == "__main__":
    # Test the fetcher
    posts = fetch_reddit_posts(subreddits=["SaaS", "Entrepreneur"], hours_ago=24)
    print(f"\n=== Filtered Posts ({len(posts)}) ===")
    for post in posts:
        print(f"\n[{post['subreddit']}] {post['title']}")
        print(f"  Link: {post['link']}")
        print(f"  Published: {post['published']}")
