#  Indeed Tech Jobs Scraper

A robust and automated Web Scraper designed to aggregate tech job listings (Software Engineering, Data Science, DevOps, etc.) from Indeed across multiple Arab and international markets.

##  Key Features (DataOps Oriented)
This project goes beyond simple scraping by implementing professional data engineering practices:
- **Automatic Checkpointing**: Saves progress periodically to local storage. If the script is interrupted, it resumes from the last saved state.
- **Resilience & Retries**: Implements a smart retry mechanism with exponential backoff to handle network flickers or temporary blocks.
- **Advanced Deduplication**: Uses Job URLs as unique identifiers to ensure no duplicate listings enter the final dataset, even across overlapping searches.
- **Anti-Blocking Measures**: Uses randomized delays and human-like behavior patterns to respect site limits and avoid IP flagging.

##  Tech Stack
* **Python**: Core logic and automation.
* **JobSpy**: Efficient job market data extraction.
* **Pandas**: Data transformation, cleaning, and structured export.
* **TQDM**: Real-time visual progress tracking in the terminal.

##  Data Schema
The output `indeed_jobs.csv` is structured for immediate analysis:
- `title`: Professional job title.
- `company`: Hiring organization.
- `location`: Specific city or region.
- `country`: Mapped country (Egypt, UAE, Saudi Arabia, USA, etc.).
- `date_posted`: Standardized date format (YYYY-MM-DD).
- `job_url`: Direct link to the job application page.

## ⚙️ Installation & Usage

1. **Install Dependencies**:
   ```bash
   pip install python-jobspy pandas tqdm
