# MECHA MIND - AI Trading & Sentiment Analysis Bot
# AI-powered sentiment analysis with adaptive learning

import os
import json
import requests
import numpy as np
from collections import deque
from solana.rpc.api import Client
from solana.publickey import PublicKey
from tweepy import OAuthHandler, API, Cursor
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

# Initialize AI Agent
ai_agent = AIAgent()

# Load Configurations
CONFIG_FILE = "config.json"
def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

config = load_config()

# Connect to Solana
solana_client = Client("https://api.mainnet-beta.solana.com")

# Twitter API Setup
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

# Risk Scoring Mechanism
def calculate_risk_score(contract_address):
    score = 100
    twitter_sentiment = analyze_twitter_sentiment(contract_address)
    if twitter_sentiment < 0:
        score -= 20
    return max(0, score)

# Dashboard Output
def print_dashboard(contract_address):
    print(f"\n[MECHA MIND] Analyzing {contract_address}...\n")
    print(f"Twitter Sentiment Score: {analyze_twitter_sentiment(contract_address)}")
    print(f"Final Risk Score: {calculate_risk_score(contract_address)}")
    print(f"Memory Log: {list(ai_agent.memory)[:5]}")

if __name__ == "__main__":
    while True:
        contract = input("Enter contract address to analyze: ")
        print_dashboard(contract)
