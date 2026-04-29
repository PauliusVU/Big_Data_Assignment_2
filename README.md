# Big_Data_Assignment_2: Quantitative ETF Screener & News Hub

A containerized Python and Streamlit web application designed to evaluate, rank, and explore the world's most heavily traded Exchange Traded Funds (ETFs) across 15 global sectors.

The core philosophy of this application is to strip away emotional investing and rely entirely on a quantitative Master Score—a multi-factor mathematical model that balances momentum, value, and risk to find the undisputed top-performing ETF in any given category.

## Disclaimer: Early Beta Version
This application is currently in an early beta phase and is for educational/research purposes only. While the Master Score is based on sound mathematical principles (Z-Score normalization), the model requires further refinement, backtesting, and weighting adjustments before it can be considered a reliable tool for real-world capital deployment. Do not use this tool as sole financial advice.

## Features
* **The Winners Circle:** Automatically scrapes and scores over 85 top ETFs across 15 sectors, displaying only the #1 top performer for each category.
* **ETF Deep Dive:** View detailed performance, risk, and fundamental metrics for the winning ETFs.
* **Live News Feed:** Integrates with the official Yahoo Finance RSS feed to pull the top 5 latest news articles for any selected ticker.
* **Custom ETF Explorer:** Look completely outside the sample. Type in any global ETF ticker to instantly pull its data, fetch its news, and calculate its hypothetical Master Score against the main database.

## The Math: How the Master Score is Calculated
The biggest challenge in quantitative finance is comparing "Apples and Oranges." You cannot simply add a P/E Ratio of 25 to a Dividend Yield of 2% and a Return of 40%.

To solve this, the Master Score uses statistical Z-Score Normalization. It completely strips away percentages, dollars, and ratios, converting every single metric into a universal currency called "Standard Deviations from the Mean."

Here is exactly how the engine works step-by-step:

### 1. The Metric Categories
The screener pulls 12 specific data points for every ETF and splits them into two categories:
* **Positive Metrics (Things we want to be HIGH):** 1-Month Return, 1-Year Return, 3-Year Return, 5-Year Return, Sharpe Ratio, and Dividend Yield.
* **Negative Metrics (Things we want to be LOW):** Volatility (Annual), Expense Ratio, P/E Ratio, P/B Ratio, Beta (3Y), and Bid-Ask Spread.

### 2. The Z-Score Formula
For every metric of every ETF, the script compares it to the average of the 85+ funds in the main database using this formula:
Z-Score = (ETF Value - Market Average) / Standard Deviation

* If an ETF is exactly average, it gets a score of 0.
* If an ETF is performing 2 standard deviations better than the group, it gets a +2.0.
* If an ETF is performing worse than the group, it gets a -1.0.

### 3. The Final Aggregation
The script loops through the metrics to calculate the final Master Score:
* It adds the Z-scores of all the Positive Metrics (e.g., A massive 5-Year return adds points).
* It subtracts the Z-scores of all the Negative Metrics (e.g., A massive Expense Ratio creates a positive Z-score, but subtracting it penalizes the ETF).

The Result: The ETF with the highest final Master Score is the one that mathematically offers the best combination of high momentum, cheap fundamentals, low fees, and responsible risk.

## Project Structure
* **app.py:** The frontend Streamlit user interface. Handles user inputs, displays the dashboards, and renders the data.
* **etf_screener.py:** The backend engine. Handles the heavy lifting of calling the Yahoo Finance API, calculating returns and risk (Sharpe, Volatility), parsing the RSS news XML feeds, and calculating the custom Master Scores.
* **requirements.txt:** Lists the exact Python dependencies needed to run the app.
* **Dockerfile:** The blueprint used to containerize the application so it can run identically on any machine in the world.

## Docker Containerization & Setup
This project was containerized utilizing official Docker documentation, specifically the "What is a container?" and "How do I run a container?" guides from the Docker Learning Center. Tutorials on the Docker Desktop app were also used to guide the setup process.

The initial Dockerfile was generated using the `docker init` command. To ensure the Streamlit application is accessible on a local machine, AI assistance was utilized to identify the correct exposed port (8501) and the necessary Streamlit configuration flag (`--server.address=0.0.0.0`).

Having set up the image, the "Run Docker Hub images" tutorial from the Learning Center was used to learn how to properly execute the run commands. Finally, the "Publish your image" tutorial from the Docker Desktop Learning Center was followed to publish the image to Docker Hub under the username **pauliusvu**.

### Build and Run Instructions
To build the Docker image, run the following command in your terminal:
```bash
docker build -t etf-screener .
```

### Publishing to Docker Hub
To tag and push the image to Docker Hub:
```bash
# Tag the image
docker tag etf-screener pauliusvu/etf-screener:v1.0

# Push to Docker Hub
docker push pauliusvu/etf-screener:v1.0
```

### Running the Published Image
To pull and run the application directly from Docker Hub, use the following command:
```bash
docker run -p 8501:8501 pauliusvu/etf-screener:v1.0
```
Once running, the application will be accessible in your browser at `http://localhost:8501`.