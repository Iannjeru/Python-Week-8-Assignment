# streamlit_app.py (large-file safe)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import io
import os

st.set_page_config(layout="wide", page_title="CORD-19 Data Explorer")

st.title("CORD-19 Metadata Explorer (Large-file safe)")
st.markdown(
    "This app can handle very large metadata CSVs by using streaming (chunked) processing. "
    "Choose **Sample** for speed, **Chunked** for low-memory aggregation, or **Full** to load everything (may OOM)."
)

# ---------- Config ----------
DEFAULT_PATH = r"C:\Users\IAN-PC\Desktop\Python\metadata_sample.csv"
file_path = st.sidebar.text_input("Local CSV path", value=DEFAULT_PATH)

mode = st.sidebar.selectbox("Load mode (choose based on RAM)", ["Chunked (low memory, recommended)", "Sample (fast)", "Full (loads all)"])

# Sample options
sample_nrows = st.sidebar.number_input("Sample rows (when Sample mode)", min_value=100, max_value=1000000, value=200000, step=10000)

# Chunk options
chunksize = st.sidebar.number_input("Chunk size (rows) when streaming", min_value=10000, max_value=1000000, value=200000, step=10000)
max_sample_rows = st.sidebar.number_input("Rows to keep as display sample (chunked mode)", min_value=10, max_value=5000, value=1000)

st.sidebar.markdown("---")
st.sidebar.write("File info")
if os.path.exists(file_path):
    st.sidebar.write(f"Exists: ✅")
    st.sidebar.write(f"Size: {os.path.getsize(file_path):,} bytes")
else:
    st.sidebar.write("Exists: ❌")

# ---------- Helpers ----------
def safe_parse_year(series):
    # returns series of years (int) with NaNs tolerated
    return pd.to_datetime(series, errors="coerce").dt.year

def plot_series_as_line(ser, title, xlabel="Year", ylabel="Count"):
    fig, ax = plt.subplots(figsize=(9, 4))
    ser.sort_index().plot(kind="line", marker="o", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    st.pyplot(fig)

def plot_series_as_bar(ser, title, xlabel="", ylabel="Count", rotate=45):
    fig, ax = plt.subplots(figsize=(9, 4))
    ser.plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.setp(ax.get_xticklabels(), rotation=rotate, ha="right")
    plt.tight_layout()
    st.pyplot(fig)

# ---------- Loading logic ----------
if not os.path.exists(file_path):
    st.error(f"File not found: {file_path}")
    st.stop()

if mode.startswith("Sample"):
    st.info(f"Loading first {sample_nrows:,} rows (fast).")
    try:
        df = pd.read_csv(file_path, nrows=sample_nrows, low_memory=False)
    except Exception as e:
        st.error(f"Error reading sample: {e}")
        st.stop()

    if "publish_time" in df.columns:
        df["publish_year"] = safe_parse_year(df["publish_time"])
    else:
        df["publish_year"] = pd.NA

    st.success(f"Sample loaded: {len(df):,} rows")
    st.markdown("**Dataset summary (sample)**")
    st.write(f"Sample rows: {len(df):,}")
    st.write(f"Years in sample: {df['publish_year'].min()} - {df['publish_year'].max()}")
    st.write(f"Unique journals (sample): {df['journal'].nunique() if 'journal' in df.columns else 'N/A'}")

    # Filters
    min_year = int(df['publish_year'].dropna().min()) if df['publish_year'].dropna().size else 2019
    max_year = int(df['publish_year'].dropna().max()) if df['publish_year'].dropna().size else 2022
    year_selection = st.slider("Select publication year range (sample)", min_year, max_year, (min_year, max_year))

    df_filtered = df[
        (df['publish_year'] >= year_selection[0]) &
        (df['publish_year'] <= year_selection[1])
    ]

    st.subheader("Filtered sample (first 10 rows)")
    st.dataframe(df_filtered.head(10))

    # plots
    if not df_filtered.empty:
        plot_series_as_line(df_filtered['publish_year'].value_counts().sort_index(), "Publications by Year (sample)")
        if 'journal' in df.columns:
            plot_series_as_bar(df_filtered['journal'].value_counts().head(10), "Top 10 Journals (sample)", xlabel="Journal")
        if 'source_x' in df.columns:
            plot_series_as_bar(df_filtered['source_x'].value_counts().head(20), "Distribution by Source (sample)", xlabel="Source", rotate=60)
    else:
        st.write("No data after filtering.")

    # download sample
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered sample as CSV", data=csv, file_name="filtered_sample.csv", mime="text/csv")

elif mode.startswith("Chunked"):
    st.info("Processing file in chunks (low memory). Aggregating counts and keeping a small sample for display.")
    # Aggregators
    year_counter = Counter()
    journal_counter = Counter()
    source_counter = Counter()
    sample_rows = []
    total_rows = 0

    try:
        for chunk in pd.read_csv(file_path, chunksize=chunksize, low_memory=False):
            total_rows += len(chunk)

            # publish_year
            if 'publish_time' in chunk.columns:
                years = safe_parse_year(chunk['publish_time'])
                year_counter.update(years.dropna().astype(int).tolist())

            # journal
            if 'journal' in chunk.columns:
                journal_counter.update(chunk['journal'].fillna("Unknown").astype(str).tolist())

            # source_x
            if 'source_x' in chunk.columns:
                source_counter.update(chunk['source_x'].fillna("Unknown").astype(str).tolist())

            # keep a small sample of rows (first N)
            if len(sample_rows) < max_sample_rows:
                rows_needed = max_sample_rows - len(sample_rows)
                sample_rows.extend(chunk.head(rows_needed).to_dict(orient="records"))

        st.success(f"Chunked processing finished — scanned {total_rows:,} rows.")
    except Exception as e:
        st.error(f"Error while streaming file: {e}")
        st.stop()

    # Build pandas Series from Counters
    year_ser = pd.Series(dict(year_counter)).sort_index()
    journal_ser = pd.Series(dict(journal_counter)).sort_values(ascending=False)
    source_ser = pd.Series(dict(source_counter)).sort_values(ascending=False)

    # Convert sample rows to DataFrame for display
    df_sample = pd.DataFrame(sample_rows)

    # Summary
    st.markdown("### Aggregated Summary (chunked)")
    st.write(f"Total rows scanned: {total_rows:,}")
    st.write(f"Years found: {int(year_ser.index.min()) if not year_ser.empty else 'N/A'} - {int(year_ser.index.max()) if not year_ser.empty else 'N/A'}")
    st.write(f"Unique journals (approx): {len(journal_ser)}")
    st.write(f"Unique sources (approx): {len(source_ser)}")

    # Filters (year range from aggregated counts)
    if not year_ser.empty:
        min_year = int(year_ser.index.min())
        max_year = int(year_ser.index.max())
    else:
        min_year, max_year = 2019, 2022

    year_selection = st.slider("Select year range (aggregated)", min_year, max_year, (min_year, max_year))

    # Show aggregated plots (filtered by year selection for year_ser)
    # Publications by year (filtered)
    if not year_ser.empty:
        filtered_year_ser = year_ser[(year_ser.index >= year_selection[0]) & (year_ser.index <= year_selection[1])]
        plot_series_as_line(filtered_year_ser, "Publications by Year (aggregated)")
    else:
        st.write("No year data available.")

    # Top journals (no year breakdown here; to do per-year you'd need per-year counters)
    if not journal_ser.empty:
        plot_series_as_bar(journal_ser.head(10), "Top 10 Journals (aggregated)", xlabel="Journal")
    else:
        st.write("No journal data available.")

    # Source distribution
    if not source_ser.empty:
        plot_series_as_bar(source_ser.head(20), "Top Sources (aggregated)", xlabel="Source", rotate=60)
    else:
        st.write("No source data available.")

    st.markdown("---")
    st.subheader("Sample rows (from the start of file)")
    if not df_sample.empty:
        st.dataframe(df_sample.head(10))
        csv_bytes = df_sample.to_csv(index=False).encode("utf-8")
        st.download_button("Download sample rows as CSV", data=csv_bytes, file_name="metadata_sample_rows.csv", mime="text/csv")
    else:
        st.write("No sample rows collected.")

else:  # Full mode
    st.warning("Full mode will attempt to load the entire CSV into memory. Only use if you have enough RAM.")
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as e:
        st.error(f"Error loading full file: {e}")
        st.stop()

    st.success(f"Loaded full DataFrame with {len(df):,} rows")
    if 'publish_time' in df.columns:
        df['publish_year'] = safe_parse_year(df['publish_time'])
    else:
        df['publish_year'] = pd.NA

    st.write("### Dataset summary (full)")
    st.write(f"Total papers: {len(df):,}")
    st.write(f"Years: {df['publish_year'].min()} - {df['publish_year'].max()}")
    if 'journal' in df.columns:
        st.write(f"Unique journals: {df['journal'].nunique()}")
    if 'source_x' in df.columns:
        st.write(f"Unique sources: {df['source_x'].nunique()}")

    # simple filters and visualizations as before
    min_year = int(df['publish_year'].min()) if df['publish_year'].notnull().any() else 2019
    max_year = int(df['publish_year'].max()) if df['publish_year'].notnull().any() else 2022
    year_selection = st.slider("Select Publication Year Range", min_value=min_year, max_value=max_year, value=(min_year, max_year))

    df_filtered = df[
        (df['publish_year'] >= year_selection[0]) &
        (df['publish_year'] <= year_selection[1])
    ]

    st.subheader("Filtered Data Sample")
    st.dataframe(df_filtered.head(10))

    if not df_filtered.empty:
        plot_series_as_line(df_filtered['publish_year'].value_counts().sort_index(), "Publications by Year (full)")
        if 'journal' in df_filtered.columns:
            plot_series_as_bar(df_filtered['journal'].value_counts().head(10), "Top 10 Journals (full)", xlabel="Journal")
        if 'source_x' in df_filtered.columns:
            plot_series_as_bar(df_filtered['source_x'].value_counts().head(20), "Distribution by Source (full)", xlabel="Source", rotate=60)

st.markdown("---")
st.write("Notes:")
st.write("- **Chunked mode** scans the whole file but only keeps small aggregates and a tiny sample; it is memory-efficient and recommended for very large files.")
st.write("- **Sample mode** is great for quick development and visualization but may not represent the whole dataset.")
st.write("- **Full mode** loads everything into memory; use only if you have sufficient RAM.")
