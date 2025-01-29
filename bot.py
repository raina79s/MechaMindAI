# MECHA MIND - AI Trading & Sentiment Analysis Bot
# Built for Solana, integrates with GMGN, SolSniffer, RugCheck, Twitter & TikTok
# Now featuring AI memory and adaptive sentiment learning

import os
import json
import requests
import numpy as np
from collections import deque
from solana.rpc.api import Client
from solana.publickey import PublicKey
from tweepy import OAuthHandler, API, Cursor
from tikapi import TikAPI
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# AI Memory for Sentiment Analysis
class AIAgent:
    def __init__(self):
        self.memory = deque(maxlen=500)
        self.vectorizer = CountVectorizer()
        self.model = MultinomialNB()
        self.trained = False
    
    def train(self, data, labels):
        vectors = self.vectorizer.fit_transform(data)
        self.model.fit(vectors, labels)
        self.trained = True
    
    def predict(self, text):
        if self.trained:
            vector = self.vectorizer.transform([text])
            return self.model.predict(vector)[0]
        return "neutral"

    def store_memory(self, text, sentiment):
        self.memory.append((text, sentiment))
        save_memory_log(text, sentiment)

# Initialize AI Agent
ai_agent = AIAgent()

# Memory Log File
MEMORY_FILE = "token_memory.json"
def save_memory_log(contract_address, sentiment):
    try:
        with open(MEMORY_FILE, "r") as file:
            memory_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        memory_data = {}
    
    memory_data[contract_address] = sentiment
    
    with open(MEMORY_FILE, "w") as file:
        json.dump(memory_data, file, indent=4)

def load_memory_log():
    try:
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

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
    sentiments = []
    for tweet in tweets:
        sentiment = ai_agent.predict(tweet.text)
        ai_agent.store_memory(tweet.text, sentiment)
        sentiments.append(1 if sentiment == "positive" else -1)
    return sum(sentiments)

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

# Dashboard Output
def print_dashboard(contract_address):
    print(f"\n[MECHA MIND] Analyzing {contract_address}...\n")
    print(f"SolSniffer Score: {get_sol_sniffer_score(contract_address)}")
    print(f"RugCheck Status: {'Safe' if is_valid_contract(contract_address) else 'Unsafe'}")
    print(f"Twitter Sentiment Score: {analyze_twitter_sentiment(contract_address)}")
    print(f"Mentioned on TikTok: {'Yes' if analyze_tiktok(contract_address) else 'No'}")
    print(f"Final Risk Score: {calculate_risk_score(contract_address)}")
    print(f"Memory Log: {list(ai_agent.memory)[:5]}")

if __name__ == "__main__":
    while True:
        contract = input("Enter contract address to analyze: ")
        print_dashboard(contract)
