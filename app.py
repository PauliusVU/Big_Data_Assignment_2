# Needed imports
import streamlit as st
import yfinance as yf
import pandas as pd

# Imports from etf_screener.py
from etf_screener import get_best_sector_etfs, get_single_etf_data, get_ticker_news, calculate_custom_score

st.set_page_config(page_title="ETF Screener", layout="wide")

# Fetching and caching the data once to avoid repeated API calls and calculations on every interaction. 
# The cache will be cleared when the user clicks the "Clear Cache & Refresh Data" button in the diagnostics section.
@st.cache_data(show_spinner="Fetching ETF data & calculating scores (this takes about a minute)")
def fetch_cached_data():
    return get_best_sector_etfs()

# Helper function to format metrics cleanly and handle missing data
def fmt(val, suffix=""):
    if pd.isna(val) or val is None:
        return "N/A"
    return f"{val}{suffix}"
    
st.title("Quantitative ETF Screener & News Hub")
st.markdown("This tool calculates a Multi-Factor Master Score to find the undisputed top-performing ETF across 15 global sectors.")

# Catch the full database (for custom math) and the winners list
try:
    full_df, df_winners = fetch_cached_data()
except ValueError:
    st.error("Please ensure your etf_screener.py returns both 'df' and 'top_per_category' at the end of get_best_sector_etfs().")
    st.stop()

st.subheader("The Winners Circle")
st.dataframe(df_winners, use_container_width=True)

st.divider()

# Individual Top-performing ETF explorer
st.subheader("Individual ETF Deep Dive")
selected_category = st.selectbox("Select a Category to inspect its top performer:", df_winners["Category/Sector"])

# Filter dataframe to the selected row
selected_row = df_winners[df_winners["Category/Sector"] == selected_category].iloc[0]
selected_ticker = selected_row["Ticker"]

st.markdown(f"### **{selected_ticker}** ({selected_category})")

st.markdown("#### Performance & Score")
p0, p1, p2, p3, p4 = st.columns(5)
p0.metric("MASTER SCORE", fmt(selected_row['Master Score']))
p1.metric("1-Month Return", fmt(selected_row["1M Return (%)"], "%"))
p2.metric("1-Year Return", fmt(selected_row["1Y Return (%)"], "%"))
p3.metric("3-Year Return", fmt(selected_row["3Y Return (%)"], "%"))
p4.metric("5-Year Return", fmt(selected_row["5Y Return (%)"], "%"))

st.markdown("#### Risk & Efficiency metrics")
r1, r2, r3, r4, r5 = st.columns(5)
r1.metric("Sharpe Ratio", fmt(selected_row["Sharpe Ratio"]))
r2.metric("Volatility (Annual)", fmt(selected_row["Volatility (%)"], "%"))
r3.metric("Beta (3Y)", fmt(selected_row["Beta"]))
r4.metric("Expense Ratio", fmt(selected_row["Expense Ratio (%)"], "%"))
r5.metric("Bid-Ask Spread", fmt(selected_row["Spread (%)"], "%"))

st.markdown("#### Fundamentals & Structure")
f1, f2, f3, f4 = st.columns(4)
f1.metric("Dividend Yield", fmt(selected_row["Yield (%)"], "%"))
f2.metric("P/E Ratio", fmt(selected_row["P/E Ratio"]))
f3.metric("P/B Ratio", fmt(selected_row["P/B Ratio"]))
f4.metric("Total Assets", fmt(selected_row["Total Assets ($B)"], " Billion"))

st.divider()

# News feed setup
st.markdown(f"#### Latest News for {selected_ticker}")
st.info("News feed powered by the official Yahoo Finance RSS (if available).")

# Fetch news from backend
news_articles = get_ticker_news(selected_ticker)

if news_articles is None:
    st.error("News feed is currently unavailable.")
elif len(news_articles) == 0:
    st.info(f"No recent news articles found in the feed for {selected_ticker}.")
else:
    for article in news_articles:
        st.markdown(f"- **[{article['title']}]({article['link']})** — *{article['pub_date']}*")

st.divider()

# Outside sample ETF explorer 
st.subheader("Custom ETF Explorer")
st.markdown("Look completely outside the sample. Type any ETF ticker to instantly pull its metrics, news, and its hypothetical Master Score.")

custom_ticker = st.text_input("Enter any ETF Ticker (e.g., JEPI, ARKK, SCHD):").upper().strip()

if custom_ticker:
    with st.spinner(f"Fetching global data for {custom_ticker}..."):
        custom_data = get_single_etf_data(custom_ticker)
        
        if custom_data:
            # Calculating the master score
            custom_data['Master Score'] = calculate_custom_score(custom_data, full_df)

            st.success(f"Data retrieved for {custom_data.get('Name', custom_data['Ticker'])} ({custom_data['Ticker']})")
            
            st.markdown("#### Performance & Score")
            cp0, cp1, cp2, cp3, cp4 = st.columns(5)
            cp0.metric("MASTER SCORE", fmt(custom_data['Master Score']))
            cp1.metric("1-Month Return", fmt(custom_data["1M Return (%)"], "%"))
            cp2.metric("1-Year Return", fmt(custom_data["1Y Return (%)"], "%"))
            cp3.metric("3-Year Return", fmt(custom_data["3Y Return (%)"], "%"))
            cp4.metric("5-Year Return", fmt(custom_data["5Y Return (%)"], "%"))

            st.markdown("#### Risk & Efficiency")
            cr1, cr2, cr3, cr4, cr5 = st.columns(5)
            cr1.metric("Sharpe Ratio", fmt(custom_data["Sharpe Ratio"]))
            cr2.metric("Volatility (Annual)", fmt(custom_data["Volatility (%)"], "%"))
            cr3.metric("Beta (3Y)", fmt(custom_data["Beta"]))
            cr4.metric("Expense Ratio", fmt(custom_data["Expense Ratio (%)"], "%"))
            cr5.metric("Bid-Ask Spread", fmt(custom_data["Spread (%)"], "%"))

            st.markdown("#### Fundamentals & Structure")
            cf1, cf2, cf3, cf4 = st.columns(4)
            cf1.metric("Dividend Yield", fmt(custom_data["Yield (%)"], "%"))
            cf2.metric("P/E Ratio", fmt(custom_data["P/E Ratio"]))
            cf3.metric("P/B Ratio", fmt(custom_data["P/B Ratio"]))
            cf4.metric("Total Assets", fmt(custom_data["Total Assets ($B)"], " Billion"))
            
            st.markdown(f"#### Latest News for {custom_data['Ticker']}")
            
            # Fetching custom ETF news from backend
            custom_news = get_ticker_news(custom_data['Ticker'])
            
            if custom_news is None:
                st.error("News feed temporarily unavailable.")
            elif len(custom_news) == 0:
                st.info("No recent news found.")
            else:
                for article in custom_news:
                    st.markdown(f"- **[{article['title']}]({article['link']})** — *{article['pub_date']}*")
        else:
            st.error(f"Could not retrieve data for '{custom_ticker}'. Ensure it is a valid, active ETF.")

st.divider()

# Diagnostics & Data Sources
with st.expander("Diagnostics & Data Sources"):
    st.markdown("""
    **Data Sources:**
    - Historical prices: Yahoo Finance API
    - News: Yahoo Finance API (when available)
    
    **Known Issues:**
    - Yahoo Finance API may be rate-limited or blocked in some network environments
    - News feeds depend on API availability and may show errors
    - Some fundamental data (P/E, P/B) may be unavailable for certain ETFs
    
    **Refresh Data:** Clear cache and rerun to fetch latest data
    """)
    
    if st.button("Clear Cache & Refresh Data"):
        st.cache_data.clear()
        st.rerun()