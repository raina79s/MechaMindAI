# MECHA MIND - AI Trading & Sentiment Analysis Bot
# Built for Solana, integrates with GMGN, SolSniffer, RugCheck, Twitter & TikTok

import os
import json
import requests
from solana.rpc.api import Client
from solana.publickey import PublicKey
from tweepy import OAuthHandler, API, Cursor
from tikapi import TikAPI

# Load Configurations
CONFIG_FILE = "config.json"
def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

config = load_config()

# Connect to Solana
solana_client = Client("https://api.mainnet-beta.solana.com")

def is_valid_contract(address):
    response = requests.get(f"https://rugcheck.xyz/api/check/{address}")
    if response.status_code == 200:
        return response.json().get("status") == "Good"
    return False

def get_sol_sniffer_score(address):
    response = requests.get(f"https://solsniffer.com/api/score/{address}")
    if response.status_code == 200:
        return response.json().get("score", 0)
    return 0

# Twitter API Connection
twitter_auth = OAuthHandler(config["twitter_api_key"], config["twitter_api_secret"])
twitter_auth.set_access_token(config["twitter_access_token"], config["twitter_access_secret"])
twitter_api = API(twitter_auth)

def analyze_twitter_sentiment(contract_address):
    tweets = Cursor(twitter_api.search_tweets, q=contract_address, lang="en").items(100)
    positive, negative = 0, 0
    for tweet in tweets:
        if any(user in tweet.text for user in config["trusted_twitter_accounts"]):
            positive += 1
        else:
            negative += 1
    return positive - negative

# TikTok API Connection
tiktok_api = TikAPI(config["tiktok_api_key"])

def analyze_tiktok(contract_name):
    response = tiktok_api.public.search_hashtags(contract_name)
    if response["status_code"] == 0:
        return len(response["data"]) > 0
    return False

# Risk Scoring Mechanism
def calculate_risk_score(contract_address):
    score = 100  # Start with a perfect score
    sol_sniffer_score = get_sol_sniffer_score(contract_address)
    if sol_sniffer_score < 80:
        score -= 40
    if not is_valid_contract(contract_address):
        score -= 50
    twitter_sentiment = analyze_twitter_sentiment(contract_address)
    if twitter_sentiment < 0:
        score -= 20
    if analyze_tiktok(contract_address):
        score += 10
    return max(0, score)

# Token Gating (Solana Wallet Check)
def is_token_holder(wallet_address):
    response = solana_client.get_token_accounts_by_owner(
        PublicKey(wallet_address),
        {'mint': PublicKey(config["token_contract_address"])}
    )
    return len(response["result"]["value"]) > 0

# Dashboard Output
def print_dashboard(contract_address):
    print(f"\n[MECHA MIND] Analyzing {contract_address}...\n")
    print(f"SolSniffer Score: {get_sol_sniffer_score(contract_address)}")
    print(f"RugCheck Status: {'Safe' if is_valid_contract(contract_address) else 'Unsafe'}")
    print(f"Twitter Sentiment Score: {analyze_twitter_sentiment(contract_address)}")
    print(f"Mentioned on TikTok: {'Yes' if analyze_tiktok(contract_address) else 'No'}")
    print(f"Final Risk Score: {calculate_risk_score(contract_address)}")

if __name__ == "__main__":
    while True:
        contract = input("Enter contract address to analyze: ")
        if is_token_holder(input("Enter your Solana wallet address: ")):
            print_dashboard(contract)
        else:
            print("Access Denied: Token required for analysis.")
