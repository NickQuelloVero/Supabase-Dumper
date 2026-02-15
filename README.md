# Supabase Dumper v2.0

A security audit tool that detects misconfigured Supabase projects by scanning for exposed API keys and testing Row Level Security (RLS) policies on database tables.

---

## What It Does

Supabase Dumper performs three phases of analysis on a target website:

1. **Recon & Config Extraction** -- Scrapes the target HTML and external JavaScript files to find Supabase project URLs and anon keys exposed in client-side code.

2. **RLS Vulnerability Scan** -- Attempts to read the OpenAPI schema from the Supabase REST endpoint. If the schema is hidden, it falls back to brute-forcing a list of common table names.

3. **Data Extraction** -- Queries each discovered table using the exposed anon key. If data is returned, the table has RLS disabled and is considered vulnerable. Results are displayed in the terminal and saved to a report file.

---

## Features

- Automatic detection of Supabase project URL and anon key from HTML/JS sources
- OpenAPI schema discovery with brute-force fallback
- Colored terminal output with ASCII art, progress bars, and animated spinners
- JSON data preview for each vulnerable table
- Clean text report saved to `supabase_full_dump.txt`
- Manual input fallback if automatic detection fails
- Security recommendations included in the final report

---

## Installation

Clone the repository:

```
git clone https://github.com/yourusername/supabase-dumper.git
cd supabase-dumper
```

Install dependencies:

```
pip install -r requirements.txt
```

---

## Usage

```
python vulntest.py
```

The tool will prompt you to enter the target URL. It accepts URLs with or without the `https://` prefix.

Example session:

```
Enter target URL > https://example.com
```

If the tool cannot detect Supabase configuration automatically, it will ask whether you want to enter the project URL and anon key manually.

---

## Output

Terminal output includes color-coded status messages, a data preview for each vulnerable table, and a summary report with statistics.

A full report with all extracted data is saved to `supabase_full_dump.txt` in the working directory. This file contains clean text without ANSI color codes.

---

## Disclaimer

This tool is intended for **authorized security testing only**. Only use it on applications you own or have explicit written permission to test. Unauthorized access to computer systems is illegal. The author is not responsible for any misuse of this tool.

---

## Requirements

- Python 3.7+
- See `requirements.txt` for package dependencies

---

## License

MIT
