# CORD-19 Metadata Explorer

An **interactive Streamlit dashboard** for exploring the COVID-19 Open Research Dataset (CORD-19) metadata.  
This project allows you to analyze publication trends, top journals, sources, and provides filtered samples **without loading the entire dataset into memory**.

---

## Features

- Load **large CSV files** safely (~1.6 GB).  
- Filter papers by **publication year**.  
- Visualize:  
  - Number of publications over time  
  - Top 10 publishing journals  
  - Distribution of papers by source  
- Download filtered samples.  
- Supports **three loading modes**:  
  1. **Sample** – Loads first N rows for fast testing.  
  2. **Chunked (recommended)** – Reads CSV in chunks, memory-efficient.  
  3. **Full** – Loads entire dataset (requires sufficient RAM).

---

## 🛠️ Requirements

- Python 3.10+  
- Libraries:

```bash
pip install pandas matplotlib streamlit
CORD19-Metadata-Explorer/
│
├─ streamlit_app.py              # Main Streamlit application
├─ metadata_sample.csv           # CORD-19 metadata CSV (~1.6 GB)
├─ venv/                         # Python virtual environment
├─ README.md                     # This file
├─ CORD19-Metadata-Analysis.ipynb# Optional analysis notebook
├─ notebooks/                    # Optional exploratory notebooks

--
Usage

1.Activate your Python virtual environmen
# Windows PowerShell
.\venv\Scripts\Activate.ps1
2.Run the Streamlit app:
python -m streamlit run streamlit_app.py

3.Open your browser at the URL printed by Streamlit (usually http://localhost:8501).
4.Select CSV path and load mode from the sidebar.
Handling the 1.6 GB CSV

Loading the full 1.6 GB metadata_sample.csv into memory can crash your machine or be extremely slow. This project uses three strategies:

Sample mode

Loads only the first N rows (sample_nrows) of the CSV.

Fast for testing and visualization, but not representative of the full dataset.

Chunked (recommended)

Reads the CSV in chunks (chunksize rows at a time).

Aggregates counts for:

Publications by year

Top journals

Source distribution

Keeps a small sample for display and download.

Extremely memory-efficient, works even on laptops with limited RAM.

Full mode

Loads the entire CSV into memory.

Only use if your system has 16+ GB RAM.

This ensures the Streamlit app remains responsive and functional with very large datasets.

📊 Visualizations

Publications by Year: Line chart showing trends over time.

Top 10 Journals: Bar chart of journals with most COVID-19 publications.

Distribution of Papers by Source: Bar chart showing which sources published papers.

Filtered Sample Download: Export CSV of filtered rows for offline analysis.

⚡ Notes

Chunked mode is highly recommended for large files.

Sample mode is useful for development/testing.

Full mode should only be used if you have enough RAM.

WordCloud visualization is disabled due to compilation issues on Windows Python 3.11.

 Summary

-This project demonstrates:
-Loading and exploring real-world datasets in Python.
-Building interactive dashboards with Streamlit.
-Handling very large datasets efficiently with chunked processing.
-Generating aggregated statistics and downloadable filtered samples.

Dataset link: https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge




