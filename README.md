# JASS Land Law Ready Reckoner v0.3.0

A local-first Windows desktop research companion for agricultural land litigation in Punjab and Haryana.

## Release 0.3.0
- Expanded the Bare Acts & Sources catalogue to 24 entries, adding land-ceiling, village-common-land, land-tenure, pre-emption, public-premises, acquisition and succession sources.
- Added an official Haryana Revenue Department consolidation-Act PDF source to the optional downloader.
- The source catalogue intentionally distinguishes direct full-text links from official portal pages; not every state Act has a verified stable direct-PDF URL.

## Included
- Home dashboard and quick research workflow
- Issue guides for threatened dispossession, mutation, partition, possession evidence, suspected forged records and inheritance
- Searchable statute references with direct official PDF links where located, official source pages, and local-copy support\n- Dedicated **Bare Acts & Sources** reader with 24 source-catalogue entries, including Haryana-specific revenue, consolidation, ceiling, tenancy, stamp, court-fee, village-common-land, pre-emption and acquisition references\n- Fetch/cache full text of BNS, BNSS and BSA from the NCRB compendium for offline reading; import TXT/HTML copies of other Acts; open locally downloaded PDFs
- Starter case-law library with principles, cautions and links to judgments
- Evidence planner with copy-to-clipboard checklist
- Private local matter notes with JSON export
- SQLite data store in the current user's application-data folder
- Source links and legal-verification warnings

## Run on Windows
Open PowerShell in this folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run.ps1
```

The launcher creates `.venv`, installs PySide6 and starts the app. Alternatively:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

## Data and privacy
The starter library is bundled in `data/seed_library.json`; official Act links are listed in `data/bare_act_sources.json`. BNS, BNSS and BSA full texts can be fetched from the NCRB compendium and cached locally from within the app. Other statutes link to official portals; the app does not bundle unverified or stale copies of every consolidated Act. Matter notes are stored locally at:
`%LOCALAPPDATA%\JASS\LandLawReadyReckoner\ready_reckoner.sqlite3`
The app does not upload matter notes. The local database is excluded from Git by `.gitignore`.

## Legal limitations
This is a research and organization tool, not legal advice. It does not contain the complete consolidated text of every statute. Case summaries are research leads. Verify current statutory text, amendments, commencement notifications, state applicability, transition rules, full judgments, paragraph numbers, later treatment, limitation and forum with a qualified advocate before relying on an entry.

## Project structure
- `app/main.py` — PySide6 user interface
- `app/database.py` — SQLite database and seed initialization
- `data/seed_library.json` — Acts, case-law leads and issue guides
- `run.ps1` — Windows launcher
