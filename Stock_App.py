import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px

# Using data caching for API data
@st.cache_data
def get_coins_list():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    if response.ok:
        coins = response.json()
        return coins
    else:
        st.error("Error fetching the coins list.")
        return []

@st.cache_data
def get_coin_history(coin_id, from_timestamp, to_timestamp):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": from_timestamp,
        "to": to_timestamp
    }
    response = requests.get(url, params=params)
    if response.ok:
        data = response.json()
        prices = data.get("prices", [])
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.date
        return df.drop(columns=["timestamp"])
    else:
        st.error(f"Error fetching the historical data for {coin_id}.")
        return pd.DataFrame(columns=["date", "price"])

def main():
    st.title("CryptoTracker")
    st.sidebar.header("Parameters")

    coins = get_coins_list()
    coin_names = [coin["name"] for coin in coins]

    selected_coin_name = st.sidebar.selectbox("Select a cryptocurrency", options=coin_names)
    selected_coin_id = next((coin["id"] for coin in coins if coin["name"] == selected_coin_name), None)

    # Date range selector
    today = datetime.now().date()
    start_date = st.sidebar.date_input('Start date', today - timedelta(days=365))
    end_date = st.sidebar.date_input('End date', today)
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    from_timestamp = int(start_datetime.timestamp())
    to_timestamp = int(end_datetime.timestamp())

    if selected_coin_id and start_date <= end_date:
        with st.spinner('Fetching data...'):
            df = get_coin_history(selected_coin_id, from_timestamp, to_timestamp)

        # Check if data is returned
        if not df.empty:
            # Create the plotly figure for the price history
            fig = px.line(df, x="date", y="price", title=f"Price of {selected_coin_name} from {start_date} to {end_date}",
                          labels={"price": "Price (USD)", "date": "Date"})
            fig.update_xaxes(rangeslider_visible=True)
            st.plotly_chart(fig, use_container_width=True)

            # Find the maximum and minimum price date
            max_price_date = df.loc[df['price'].idxmax()]['date']
            min_price_date = df.loc[df['price'].idxmin()]['date']

            # Find the maximum and minimum price and format them to 12 decimal places
            max_price = df['price'].max()
            min_price = df['price'].min()
            max_price_formatted = f"{max_price:.12f}"
            min_price_formatted = f"{min_price:.12f}"

            # Display the metrics for maximum and minimum prices with dates
            col1, col2 = st.columns(2)
            col1.metric("Maximum Price", f"${max_price_formatted}", f"Date: {max_price_date}")
            col2.metric("Minimum Price", f"${min_price_formatted}", f"Date: {min_price_date}")
        else:
            st.error("No data available for the selected cryptocurrency and date range.")
    else:
        st.info("Please select a cryptocurrency and a valid date range where the start date is not after the end date.")

if __name__ == "__main__":
    main()
