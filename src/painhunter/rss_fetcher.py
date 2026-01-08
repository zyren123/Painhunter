"""RSS Fetcher module for Reddit pain point discovery."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict
import feedparser
import httpx


# Reddit RSS endpoint
REDDIT_RSS_BASE = "https://www.reddit.com/r/{subreddit}/new/.rss"

# User-Agent to mimic browser and avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Keywords for filtering pain point posts
KEYWORDS = [
    # Demand patterns
    "is there an app",
    "anyone know a tool",
    "how do I",
    # Complaint patterns
    "frustrated with",
    "too expensive",
    "struggling with",
    "hate it when",
    # Efficiency patterns
    "manual task",
    "waste of time",
    "tedious",
    # Additional
    "how to",
    "tool",
]


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


def contains_keyword(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """Check if text contains any of the keywords."""
    text_to_check = text if case_sensitive else text.lower()
    for keyword in keywords:
        keyword_to_check = keyword if case_sensitive else keyword.lower()
        if keyword_to_check in text_to_check:
            return True
    return False


def fetch_subreddit_posts(subreddit: str, hours_ago: int = 24) -> List[Dict]:
    """Fetch posts from a subreddit's RSS feed within the specified time window."""
    url = REDDIT_RSS_BASE.format(subreddit=subreddit)
    posts = []

    with httpx.Client(headers=HEADERS, timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        for entry in feed.entries:
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


def filter_by_keywords(posts: List[Dict], keywords: List[str] = None) -> List[Dict]:
    """Filter posts that contain any of the specified keywords in title or summary."""
    if keywords is None:
        keywords = KEYWORDS

    filtered = []
    for post in posts:
        text_to_check = f"{post['title']} {post['summary']}"
        if contains_keyword(text_to_check, keywords):
            filtered.append(post)
    return filtered


def fetch_reddit_posts(
    subreddits: List[str] = None,
    keywords: List[str] = None,
    hours_ago: int = 24,
) -> List[Dict]:
    """Main function to fetch and filter Reddit posts.

    Args:
        subreddits: List of subreddit names (without 'r/')
        keywords: List of keywords to filter by
        hours_ago: Only fetch posts from the last N hours

    Returns:
        List of filtered post dictionaries
    """
    if subreddits is None:
        subreddits = ["SaaS", "Entrepreneur"]

    all_posts = []
    for subreddit in subreddits:
        print(f"Fetching posts from r/{subreddit}...")
        posts = fetch_subreddit_posts(subreddit, hours_ago)
        print(f"  Found {len(posts)} posts in the last {hours_ago} hours")
        all_posts.extend(posts)

    print(f"\nTotal posts fetched: {len(all_posts)}")

    # Filter by keywords
    filtered_posts = filter_by_keywords(all_posts, keywords)
    print(f"Posts matching keywords: {len(filtered_posts)}")

    return filtered_posts


if __name__ == "__main__":
    # Test the fetcher
    posts = fetch_reddit_posts(subreddits=["SaaS", "Entrepreneur"], hours_ago=24)
    print(f"\n=== Filtered Posts ({len(posts)}) ===")
    for post in posts:
        print(f"\n[{post['subreddit']}] {post['title']}")
        print(f"  Link: {post['link']}")
        print(f"  Published: {post['published']}")
