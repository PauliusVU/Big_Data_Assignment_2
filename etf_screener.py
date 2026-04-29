# Imports
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET
import time   
import random 

# Set global option to avoid downcasting warnings in future Pandas versions
pd.set_option('future.no_silent_downcasting', True)

# Get expense ratio with multiple fallback methods to handle inconsistencies in yfinance data
def get_expense_ratio_fallback(ticker_symbol, info):

    expense_ratio = None
    
    # Method 1: fundProfile nested in info dict (looks inside the info dictionary)
    try:
        if 'fundProfile' in info and info['fundProfile']:
            expense_ratio = info['fundProfile'].get('feesExpensesInvestment', {}).get('annualReportExpenseRatio')
    except:
        pass
    
    # Method 2: Checking various keys in the main info dict if Method 1 fails
    if expense_ratio is None:
        expense_ratio = (
            info.get('annualReportExpenseRatio') or
            info.get('expenseRatio') or
            info.get('totalExpenses') or
            info.get('netExpenseRatio')
        )
    
    # Converting to percentage if value is found
    if expense_ratio is not None:
        try:
            # If it's already a percentage (> 1) no multiplication is applied
            if expense_ratio < 1:
                expense_ratio = float(expense_ratio) * 100
            else:
                expense_ratio = float(expense_ratio)
        except:
            expense_ratio = None
    
    return expense_ratio

def get_best_sector_etfs():
    sector_etfs = {
        "Broad Market US": ["SPY", "VOO", "IVV", "VTI", "QQQ", "IWM", "DIA"], 
        "Global / World": ["VT", "ACWI", "URTH", "IOO", "VXUS"], 
        "Intl Developed": ["VEA", "IEFA", "EFA", "SCHF", "IDEV"],
        "Emerging Markets": ["VWO", "IEMG", "EEM", "SCHE", "SPEM"],
        "Technology": ["XLK", "VGT", "IYW", "FTEC", "IXN", "SMH"], 
        "Financials": ["XLF", "VFH", "IYF", "FNCL", "IXG", "KRE"], 
        "Health Care": ["XLV", "VHT", "IYH", "FHLC", "IXJ", "IBB"],
        "Industrials": ["XLI", "VIS", "IYJ", "FIDU", "EXI", "ITA"],
        "Energy": ["XLE", "VDE", "IYE", "FENY", "IXC", "XOP"],
        "Cons Discretionary": ["XLY", "VCR", "IYC", "FDIS", "RXI"],
        "Cons Staples": ["XLP", "VDC", "IYK", "FSTA", "KXI"],
        "Comm Services": ["XLC", "VOX", "IYZ", "FCOM", "IXP"],
        "Utilities": ["XLU", "VPU", "IDU", "FUTY", "JXI"],
        "Real Estate": ["XLRE", "VNQ", "IYR", "FREL", "VNQI", "SCHH"], 
        "Materials": ["XLB", "VAW", "IYM", "FMAT", "MXI", "GDX"],
        "Dividend & Value": ["SCHD", "VYM", "VIG", "DVY", "SDY"],
        "Commodities & Gold": ["GLD", "IAU", "SLV", "PDBC", "GSG"]
    }
    etf_data = []
    print("Fetching data and calculating scores. This may take a minute...")
    
    # Loop through each sector and its ETFs, fetching data and calculating metrics
    for sector, tickers in sector_etfs.items():
        for ticker_symbol in tickers:
            try:
                # Adding a randomized delay to prevent Yahoo blocking
                time.sleep(random.uniform(1.5, 3.0))

                ticker = yf.Ticker(ticker_symbol)
                
                # Try to get info, but have a fallback
                try:
                    info = ticker.info
                except:
                    info = {}
                    print(f"Warning: Could not fetch info for {ticker_symbol}, using limited data")
                
                # Fetch 5-year history in one block, if possible 
                hist = ticker.history(period="5y", auto_adjust=True)
                
                # 'hist is None or' added to prevent NoneType subscript crashes!
                if hist is None or hist.empty or len(hist) < 21: 
                    print(f"Skipping {ticker_symbol} - insufficient history")
                    continue
                
                # Grabbing the close price series for performance calculations
                close = hist["Close"]
                # Most recent price
                current_price = close.iloc[-1]
                last_date = close.index[-1]
                years_covered = (last_date - close.index[0]).days / 365.25
                
                # Performance Calculations
                monthly_return = ((current_price - close.iloc[-21]) / close.iloc[-21]) * 100 if len(close) >= 21 else None
                
                current_year = datetime.now().year
                ytd_data = hist[hist.index.year == current_year]
                ytd_return = ((current_price - ytd_data["Close"].iloc[0]) / ytd_data["Close"].iloc[0]) * 100 if len(ytd_data) > 1 else None
                
                one_year_return = None
                if years_covered >= 0.95:
                    target_1y = last_date - pd.Timedelta(days=365)
                    idx_1y = close.index.get_indexer([target_1y], method='nearest')[0]
                    one_year_return = ((current_price - close.iloc[idx_1y]) / close.iloc[idx_1y]) * 100
                
                three_year_return = None
                if years_covered >= 2.95:
                    target_3y = last_date - pd.Timedelta(days=1095)
                    idx_3y = close.index.get_indexer([target_3y], method='nearest')[0]
                    three_year_return = ((current_price - close.iloc[idx_3y]) / close.iloc[idx_3y]) * 100
                
                five_year_return = None
                if years_covered >= 4.95:
                    target_5y = last_date - pd.Timedelta(days=1825)
                    idx_5y = close.index.get_indexer([target_5y], method='nearest')[0]
                    five_year_return = ((current_price - close.iloc[idx_5y]) / close.iloc[idx_5y]) * 100
                
                # Risk Calculations (Calculated fo 1-year period for comparison (past 252 trading days))
                returns_1y = close.tail(252).pct_change().dropna()
                volatility = returns_1y.std() * (252 ** 0.5)
                sharpe = (returns_1y.mean() / returns_1y.std()) * (252 ** 0.5) if returns_1y.std() != 0 else None
                
                # Fundamental/Structural metrics - latest available from info dict
                trailing_pe = info.get('trailingPE')
                price_to_book = info.get('priceToBook')
                
                div_yield = info.get('yield', info.get('trailingAnnualDividendYield'))
                if div_yield is not None:
                    div_yield = div_yield * 100
                
                beta = info.get('beta3Year', info.get('beta'))
                
                # Get expense ratio with fallback
                expense_ratio = get_expense_ratio_fallback(ticker_symbol, info)
                
                bid, ask = info.get('bid'), info.get('ask')
                spread_pct = ((ask - bid) / ask) * 100 if bid and ask and ask > 0 else None
                
                raw_assets = info.get('totalAssets')
                assets_billions = round(raw_assets / 1_000_000_000, 2) if raw_assets else None
                
                etf_data.append({
                    "Category/Sector": sector,
                    "Ticker": ticker_symbol,
                    "1M Return (%)": monthly_return,
                    "1Y Return (%)": one_year_return,
                    "3Y Return (%)": three_year_return,
                    "5Y Return (%)": five_year_return,
                    "Volatility (%)": volatility * 100 if volatility else None,
                    "Sharpe Ratio": sharpe,
                    "Expense Ratio (%)": expense_ratio,
                    "Yield (%)": div_yield,
                    "P/E Ratio": trailing_pe,
                    "P/B Ratio": price_to_book,
                    "Beta": beta,
                    "Spread (%)": spread_pct,
                    "Total Assets ($B)": assets_billions,
                })
                
            except Exception as e:
                print(f"Error fetching {ticker_symbol}: {e}")
                continue
    
    df = pd.DataFrame(etf_data)

    # Guard Clause to prevent crash if data fetch fails
    if df.empty:
        print("CRITICAL: No data retrieved. Check your internet or API limits.")
        return pd.DataFrame(), pd.DataFrame(columns=["Category/Sector", "Ticker", "Master Score"])
    
    # Define which metrics are positive (higher is better) and which are negative (lower is better) for the Master Score calculation
    positive_metrics = ["1M Return (%)", "1Y Return (%)", "3Y Return (%)", "5Y Return (%)", "Sharpe Ratio", "Yield (%)"]
    negative_metrics = ["Volatility (%)", "Expense Ratio (%)", "P/E Ratio", "P/B Ratio", "Beta", "Spread (%)"]
    
    # Force columns to be numeric
    cols_to_fix = positive_metrics + negative_metrics
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Z-score normalization and Master Score calculation
    df["Master Score"] = 0.0
    
    for col in positive_metrics:
        # Safety check to ensure we have valid data and avoid division by zero
        if col in df.columns and df[col].notna().sum() > 0 and df[col].std() > 0:
            # Z-score calculuation
            z_score = (df[col] - df[col].mean()) / df[col].std()
            df["Master Score"] += z_score.fillna(0)
    
    for col in negative_metrics:
        if col in df.columns and df[col].notna().sum() > 0 and df[col].std() > 0:
            z_score = (df[col] - df[col].mean()) / df[col].std()
            df["Master Score"] += (z_score * -1).fillna(0)
    
    # Ensure Master Score is numeric
    df["Master Score"] = pd.to_numeric(df["Master Score"], errors='coerce').fillna(0)
    df["Master Score"] = df["Master Score"].round(2)
    
    # Filter for top performer per category
    top_per_category = df.loc[df.groupby("Category/Sector")["Master Score"].idxmax()]
    top_per_category = top_per_category.sort_values(by="Master Score", ascending=False).reset_index(drop=True)
   
    # Return the full DataFrame and the winners
    return df, top_per_category

# Fetches and calculates all metrics for any custom selected ETF ticker. 
# This is the same logic as the main function but for a single ticker, and is used for the custom ETF explorer section in the Streamlit app.
def get_single_etf_data(ticker_symbol):
    ticker_symbol = ticker_symbol.upper().strip()
    try:
        ticker = yf.Ticker(ticker_symbol)
        try:
            info = ticker.info
        except:
            info = {}

        hist = ticker.history(period="5y", auto_adjust=True)
        
        # 'hist is None or' added to prevent NoneType subscript crashes
        if hist is None or hist.empty or len(hist) < 21:
            return None 

        close = hist["Close"]
        current_price = close.iloc[-1]
        last_date = close.index[-1]
        years_covered = (last_date - close.index[0]).days / 365.25

        # Performance Calculations
        monthly_return = ((current_price - close.iloc[-21]) / close.iloc[-21]) * 100 if len(close) >= 21 else None

        current_year = datetime.now().year
        ytd_data = hist[hist.index.year == current_year]
        ytd_return = ((current_price - ytd_data["Close"].iloc[0]) / ytd_data["Close"].iloc[0]) * 100 if len(ytd_data) > 1 else None

        one_year_return = None
        if years_covered >= 0.95:
            target_1y = last_date - pd.Timedelta(days=365)
            idx_1y = close.index.get_indexer([target_1y], method='nearest')[0]
            one_year_return = ((current_price - close.iloc[idx_1y]) / close.iloc[idx_1y]) * 100

        three_year_return = None
        if years_covered >= 2.95:
            target_3y = last_date - pd.Timedelta(days=1095)
            idx_3y = close.index.get_indexer([target_3y], method='nearest')[0]
            three_year_return = ((current_price - close.iloc[idx_3y]) / close.iloc[idx_3y]) * 100

        five_year_return = None
        if years_covered >= 4.95:
            target_5y = last_date - pd.Timedelta(days=1825)
            idx_5y = close.index.get_indexer([target_5y], method='nearest')[0]
            five_year_return = ((current_price - close.iloc[idx_5y]) / close.iloc[idx_5y]) * 100

        returns_1y = close.tail(252).pct_change().dropna()
        volatility = returns_1y.std() * (252 ** 0.5)
        sharpe = (returns_1y.mean() / returns_1y.std()) * (252 ** 0.5) if returns_1y.std() != 0 else None

        trailing_pe = info.get('trailingPE')
        price_to_book = info.get('priceToBook')
        div_yield = info.get('yield', info.get('trailingAnnualDividendYield'))
        if div_yield is not None: div_yield = div_yield * 100
        beta = info.get('beta3Year', info.get('beta'))
        expense_ratio = get_expense_ratio_fallback(ticker_symbol, info)
        
        bid, ask = info.get('bid'), info.get('ask')
        spread_pct = ((ask - bid) / ask) * 100 if bid and ask and ask > 0 else None
        
        raw_assets = info.get('totalAssets')
        assets_billions = round(raw_assets / 1_000_000_000, 2) if raw_assets else None

        return {
            "Ticker": ticker_symbol,
            "Name": info.get('shortName', ticker_symbol),
            "1M Return (%)": monthly_return, "1Y Return (%)": one_year_return,
            "3Y Return (%)": three_year_return, "5Y Return (%)": five_year_return,
            "Volatility (%)": volatility * 100 if volatility else None, "Sharpe Ratio": sharpe,
            "Expense Ratio (%)": expense_ratio, "Yield (%)": div_yield,
            "P/E Ratio": trailing_pe, "P/B Ratio": price_to_book,
            "Beta": beta, "Spread (%)": spread_pct, "Total Assets ($B)": assets_billions,
        }
    except Exception as e:
        return None

# Calculates the Master Score for a custom ETF based on the same logic as the main DataFrame, allowing for comparison against the top performers.
def calculate_custom_score(custom_data, full_df):
    positive_metrics = ["1M Return (%)", "1Y Return (%)", "3Y Return (%)", "5Y Return (%)", "Sharpe Ratio", "Yield (%)"]
    negative_metrics = ["Volatility (%)", "Expense Ratio (%)", "P/E Ratio", "P/B Ratio", "Beta", "Spread (%)"]
    
    custom_score = 0.0
    
    for col in positive_metrics:
        val = custom_data.get(col)
        if val is not None and full_df[col].std() > 0:
            custom_score += (val - full_df[col].mean()) / full_df[col].std()
            
    for col in negative_metrics:
        val = custom_data.get(col)
        if val is not None and full_df[col].std() > 0:
            custom_score -= (val - full_df[col].mean()) / full_df[col].std()
            
    return round(custom_score, 2)

# Fetches and parses the latest news articles for a given ticker from Yahoo Finance RSS.
def get_ticker_news(ticker_symbol):
    articles_list = []
    # Accessing Yahoo Finance for ETF news via RSS feed. 
    try:
        rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker_symbol}"
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        # Go to the page and read the XML data, download it
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()

        # Reading the XML data and parsing it to extract news articles.    
        root = ET.fromstring(xml_data)
        articles = root.findall('.//item')
        
        if articles:
            # 5 latest articles. Extracts information about the article, such as title, link, and publication date, and stores it in a list of dictionaries.
            for item in articles[:5]:
                title = item.find('title').text if item.find('title') is not None else "No Title"
                link = item.find('link').text if item.find('link') is not None else "#"
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                if pub_date: 
                    pub_date = pub_date[:16]
                
                # Packaging articles into a clean dictionary
                articles_list.append({"title": title, "link": link, "pub_date": pub_date})
                
        return articles_list
    except Exception as e:
        # Return None if the network request fails
        return None  

# Setting up to allow running as part of the app or standalone for testing
if __name__ == "__main__":
    print("Running ETF Screener in standalone mode")
    df_winners = get_best_sector_etfs()
    print(df_winners.to_string(index=False))