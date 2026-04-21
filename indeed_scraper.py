"""
Indeed Tech Jobs Scraper
========================
Scrapes tech job listings from Indeed across major Arab and foreign countries.
Handles pagination, retries, deduplication, and checkpointing automatically.

Output: indeed_jobs.csv

Usage:
    pip install python-jobspy pandas tqdm
    python indeed_scraper.py
"""

import pandas as pd
import time
import random
import os
from tqdm import tqdm

try:
    from jobspy import scrape_jobs
except ImportError:
    print("ERROR: jobspy is not installed. Run:")
    print("   pip install python-jobspy")
    exit(1)


# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

# Job titles to search for across all locations
KEYWORDS = [
    # Development
    "software engineer",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "mobile developer",
    "ios developer",
    "android developer",
    "web developer",
    # Data & AI
    "data scientist",
    "data analyst",
    "data engineer",
    "machine learning engineer",
    "AI engineer",
    "business intelligence",
    "nlp engineer",
    "computer vision engineer",
    # Infrastructure & Security
    "devops engineer",
    "cloud engineer",
    "site reliability engineer",
    "cybersecurity engineer",
    "network engineer",
    "linux administrator",
    # Product & Design
    "product manager",
    "product designer",
    "UX designer",
    "UI designer",
    "UX researcher",
    # Other Tech
    "QA engineer",
    "blockchain developer",
    "game developer",
]

# Target countries — key is the display name, value is the Indeed country string
LOCATIONS = {
    # Arab countries
    "Egypt":          "egypt",
    "Saudi Arabia":   "saudi arabia",
    "UAE":            "united arab emirates",
    "Qatar":          "qatar",
    "Kuwait":         "kuwait",
    # Foreign countries
    "United States":  "usa",
    "United Kingdom": "united kingdom",
    "Germany":        "germany",
    "Canada":         "canada",
    "Netherlands":    "netherlands",
}

# Number of results to fetch per keyword/location combination
RESULTS_PER_SEARCH = 50

# Random delay between requests to avoid rate limiting (in seconds)
DELAY_MIN = 8
DELAY_MAX = 15

# Output files
OUTPUT_FILE     = "indeed_jobs.csv"
CHECKPOINT_FILE = "indeed_checkpoint.csv"  # Temporary file to resume on failure


# ─────────────────────────────────────────────
# Columns to keep in the final CSV
# ─────────────────────────────────────────────

COLUMNS = [
    "title",       # Job title
    "company",     # Company name
    "location",    # City / region
    "country",     # Country (added by us)
    "date_posted", # Posting date
    "job_type",    # Full-time, part-time, remote, etc.
    "job_url",     # Direct link to the job posting
]


# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────

def load_checkpoint():
    """Load previously saved progress so we can resume if the script was interrupted."""
    if os.path.exists(CHECKPOINT_FILE):
        print("Checkpoint found. Resuming from last saved point...")
        return pd.read_csv(CHECKPOINT_FILE)
    return pd.DataFrame()


def save_checkpoint(df):
    """Save current progress to a temporary CSV file."""
    df.to_csv(CHECKPOINT_FILE, index=False, encoding="utf-8-sig")


def clean_dataframe(df, country_name):
    """
    Normalize and clean a scraped dataframe:
    - Keep only the columns we need
    - Add the country column
    - Standardize date format
    - Strip whitespace from text fields
    """
    # Keep only available columns from our list
    available = [c for c in COLUMNS if c in df.columns]
    df = df[available].copy()

    # Tag each row with the country it was scraped from
    df["country"] = country_name

    # Standardize date to YYYY-MM-DD
    if "date_posted" in df.columns:
        df["date_posted"] = pd.to_datetime(
            df["date_posted"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Strip extra whitespace from text columns
    for col in ["title", "company", "location"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


def scrape_with_retry(keyword, location_name, country_code, retries=3):
    """
    Scrape Indeed for a given keyword and location.
    Retries up to 3 times with increasing wait time on failure.
    Returns an empty DataFrame if all attempts fail.
    """
    for attempt in range(1, retries + 1):
        try:
            jobs = scrape_jobs(
                site_name=["indeed"],
                search_term=keyword,
                location=location_name,
                country_indeed=country_code,
                results_wanted=RESULTS_PER_SEARCH,
                hours_old=72 * 30,  # Jobs posted in the last ~30 days
                verbose=0,
            )
            return jobs
        except Exception as e:
            wait = attempt * 10
            print(f"      Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                print(f"      Waiting {wait} seconds before retry...")
                time.sleep(wait)

    # Return empty DataFrame if all retries failed
    return pd.DataFrame()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Indeed Tech Jobs Scraper")
    print(f"  {len(KEYWORDS)} keywords x {len(LOCATIONS)} locations")
    print(f"  Total searches: {len(KEYWORDS) * len(LOCATIONS)}")
    print("=" * 55)

    # Load checkpoint data if available
    all_jobs = load_checkpoint()

    # Track already seen URLs to avoid duplicates across searches
    seen_urls = set(all_jobs["job_url"].tolist()) if not all_jobs.empty else set()

    total_searches = len(KEYWORDS) * len(LOCATIONS)
    search_count   = 0
    new_jobs_total = 0

    # Progress bar to track overall scraping progress
    pbar = tqdm(total=total_searches, desc="Overall Progress", unit="search")

    for location_name, country_code in LOCATIONS.items():
        for keyword in KEYWORDS:
            search_count += 1

            # Update progress bar label
            pbar.set_postfix({
                "location": location_name[:10],
                "keyword":  keyword[:15],
                "total":    len(all_jobs),
            })

            # Scrape jobs for this keyword + location
            df = scrape_with_retry(keyword, location_name, country_code)

            if not df.empty:
                df = clean_dataframe(df, location_name)

                # Remove jobs we've already collected
                if "job_url" in df.columns:
                    df = df[~df["job_url"].isin(seen_urls)]
                    seen_urls.update(df["job_url"].tolist())

                if not df.empty:
                    new_jobs_total += len(df)
                    all_jobs = pd.concat([all_jobs, df], ignore_index=True)

            # Save checkpoint every 10 searches in case of interruption
            if search_count % 10 == 0 and not all_jobs.empty:
                save_checkpoint(all_jobs)
                tqdm.write(f"  Checkpoint saved — {len(all_jobs)} jobs so far")

            pbar.update(1)

            # Random delay to reduce the chance of getting blocked
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    pbar.close()

    # ─────────────────────────────────────────
    # Save final output
    # ─────────────────────────────────────────

    if all_jobs.empty:
        print("\nNo data collected.")
        return

    # Final deduplication by job URL
    if "job_url" in all_jobs.columns:
        before = len(all_jobs)
        all_jobs = all_jobs.drop_duplicates(subset=["job_url"])
        removed = before - len(all_jobs)
        if removed:
            print(f"\nRemoved {removed} duplicate entries.")

    # Sort by most recent postings first
    if "date_posted" in all_jobs.columns:
        all_jobs = all_jobs.sort_values("date_posted", ascending=False)

    # Save to CSV with UTF-8 BOM for Excel compatibility
    all_jobs.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    # Clean up checkpoint file after successful completion
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    # ─────────────────────────────────────────
    # Print summary
    # ─────────────────────────────────────────

    print("\n" + "=" * 55)
    print(f"  Done! Output saved to: {OUTPUT_FILE}")
    print(f"  Total jobs collected: {len(all_jobs):,}")
    print(f"  New unique jobs: {new_jobs_total:,}")

    print("\n  Jobs by country:")
    if "country" in all_jobs.columns:
        for country, count in all_jobs["country"].value_counts().items():
            print(f"    {country:<20} {count:>5,}")

    print("\n  Top job titles:")
    if "title" in all_jobs.columns:
        for title, count in all_jobs["title"].value_counts().head(5).items():
            print(f"    {title:<35} {count:>4,}")

    print("=" * 55)


if __name__ == "__main__":
    main()