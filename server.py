from flask import Flask, request, jsonify, send_from_directory
import os
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from gtts import gTTS
from googletrans import Translator
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Directory for storing audio files
AUDIO_FOLDER = 'audio_files'
os.makedirs(AUDIO_FOLDER, exist_ok=True)
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

# Function to get news articles
def get_news_bing(company_name):
    search_url = f"https://www.bing.com/news/search?q={company_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for result in soup.select(".news-card"):
        title_tag = result.select_one("a.title")
        snippet_tag = result.select_one(".snippet")
        link = title_tag["href"] if title_tag else ""
        
        if title_tag and snippet_tag:
            articles.append({
                "title": title_tag.get_text(),
                "summary": snippet_tag.get_text(),
                "link": link,
            })

        if len(articles) >= 10:
            break

    return articles

# Sentiment Analysis
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)["compound"]
    return "Positive" if score >= 0.05 else "Negative" if score <= -0.05 else "Neutral"

# Generate Hindi Speech
def generate_hindi_speech(text, company_name):
    tts = gTTS(text=text, lang='hi')
    audio_file = f"{company_name}_news_summary.mp3"
    audio_path = os.path.join(AUDIO_FOLDER, audio_file)
    tts.save(audio_path)

# Serve Audio
@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(app.config['AUDIO_FOLDER'], filename)

# API to Fetch News and Analyze Sentiment
@app.route('/get_news', methods=['GET'])
def get_news():
    company_name = request.args.get('company_name', '')
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400

    news_articles = get_news_bing(company_name)
    if news_articles:
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        detailed_articles = []
        translator = Translator()

        summary_text = f"{company_name} कंपनी के समाचार सारांश:\n\n"

        for idx, article in enumerate(news_articles, 1):
            title, summary = article["title"], article["summary"]
            sentiment = analyze_sentiment(summary)
            sentiment_counts[sentiment] += 1

            title_hindi = translator.translate(title, src='en', dest='hi').text
            summary_hindi = translator.translate(summary, src='en', dest='hi').text
            sentiment_hindi = {"Positive": "सकारात्मक", "Negative": "नकारात्मक", "Neutral": "तटस्थ"}[sentiment]

            detailed_articles.append({"title": title, "summary": summary, "sentiment": sentiment})
            summary_text += f"समाचार {idx}: {title_hindi}\nसंक्षेप: {summary_hindi}\nभावना: {sentiment_hindi}\n\n"

        overall_sentiment = "✅ समग्र भावना: सकारात्मक" if sentiment_counts["Positive"] > sentiment_counts["Negative"] else \
                            "❌ समग्र भावना: नकारात्मक" if sentiment_counts["Negative"] > sentiment_counts["Positive"] else \
                            "⚖️ समग्र भावना: संतुलित या तटस्थ"

        summary_text += f"\n{overall_sentiment}"
        generate_hindi_speech(summary_text, company_name)

        return jsonify({
            "detailed_articles": detailed_articles,
            "sentiment_counts": sentiment_counts,
            "overall_sentiment": overall_sentiment,
            "audio_file": f"{company_name}_news_summary.mp3"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)  # Hugging Face runs on port 7860
