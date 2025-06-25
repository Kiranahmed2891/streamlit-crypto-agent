import streamlit as st
import requests
import os
import dotenv
import asyncio

from agents import (
    OpenAIChatCompletionsModel, Agent, Runner,
    set_tracing_disabled, AsyncOpenAI, function_tool
)

# Load environment variables
dotenv.load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Disable tracing
set_tracing_disabled(True)

# Setup Gemini client
client = AsyncOpenAI(
    base_url='https://generativelanguage.googleapis.com/v1beta/openai/.',
    api_key=GEMINI_API_KEY
)

# Initialize model
model = OpenAIChatCompletionsModel("gemini-2.0-flash", openai_client=client)

# Define the crypto price tool
@function_tool
def get_crypto_price(name: str):
    """Get real-time price of a cryptocurrency."""
    coins = requests.get("https://api.coinlore.net/api/tickers/").json()["data"]
    for coin in coins:
        if coin['name'].lower() == name.lower() or \
           coin['symbol'].lower() == name.lower() or \
           coin['nameid'] == name.lower():
            return {"name": coin["name"], "symbol": coin["symbol"], "price_usd": coin["price_usd"]}
    return {"error": f"Coin '{name}' not found."}

# Define the agent
CryptoDataAgent = Agent(
    name="CryptoDataAgent",
    instructions="You are a Crypto Agent. You provide real-time rates using get_crypto_price tool. EXPECT the user always asks about coins. NEVER respond to any other TOPIC.",
    model=model,
    tools=[get_crypto_price],
)

# Streamlit App
st.title("💰 Crypto Agent Powered by Gemini + Coinlore")

coin_name = st.text_input("Enter crypto name or symbol (e.g., BTC, ethereum, solana):")

if st.button("Get Price"):
    if coin_name:
        with st.spinner("Fetching price..."):
            async def get_response():
                return await Runner.run(CryptoDataAgent, f"What is the price of {coin_name}?")
            result = asyncio.run(get_response())
            st.success(result.final_output)
    else:
        st.warning("Please enter a coin name or symbol.")
