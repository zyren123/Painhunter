import os
from datetime import datetime
from dotenv import load_dotenv
from src.painhunter.rss_fetcher import fetch_reddit_posts
from src.painhunter.analyzer import analyze_pain_points_by_source, print_analysis_report
from src.painhunter.emailer import send_report, generate_html_report


# Load .env file
load_dotenv()


def main():
    """Main entry point for Painhunter."""
    print("=== Painhunter: Reddit Pain Point Hunter ===\n")

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Skipping AI analysis.")
        print("Please set it in .env file")
        return

    # Fetch and filter posts
    posts = fetch_reddit_posts(
        subreddits=["SaaS", "Entrepreneur", "SideProject", "smallbusiness"],
        hours_ago=24,
    )

    # Display filtered posts
    print(f"\n=== Filtered Posts ({len(posts)}) ===")
    for post in posts:
        print(f"\n[{post['subreddit']}] {post['title']}")
        print(f"  Link: {post['link']}")

    # AI Analysis
    if posts:
        analysis = analyze_pain_points_by_source(posts)
        print_analysis_report(analysis)

        # Generate and save HTML report
        html_report = generate_html_report(analysis)
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_filename = f"/tmp/painhunter_report_{date_str}.html"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(html_report)
        print(f"\nHTML report saved to: {report_filename}")

        # Try to send email report
        print("\nAttempting to send email report...")
        if send_report(analysis):
            print("Email sent successfully!")
        else:
            print("Email not sent (missing SMTP config). Report generated only.")


if __name__ == "__main__":
    main()
