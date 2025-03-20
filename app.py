import streamlit as st
import requests

st.title("News Sentiment Analysis")
company_name = st.text_input("Enter Company Name", "")

API_URL = "http://127.0.0.1:7860/get_news"

if company_name:
    try:
        response = requests.get(f"{API_URL}?company_name={company_name}")
        print("Raw API Response:", response.text)  # Debugging

        if response.status_code == 200:
            data = response.json()
            
            if "detailed_articles" not in data:
                st.error("Unexpected API response format. Check backend output.")
                st.json(data)  # Show response for debugging
            else:
                for idx, article in enumerate(data['detailed_articles'], 1):
                    st.subheader(f"{idx}. Title: {article['title']}")
                    st.write(f"Summary: {article['summary']}")
                    st.write(f"Sentiment: {article['sentiment']}")
                    st.markdown("-" * 80)

                st.write("🔹 Positive Articles:", data['sentiment_counts']['Positive'])
                st.write("🔸 Negative Articles:", data['sentiment_counts']['Negative'])
                st.write("⚪ Neutral Articles:", data['sentiment_counts']['Neutral'])
                st.write(f"{data['overall_sentiment']}")

                st.success("🔊 Hindi Audio Summary Saved!")
                audio_url = f"http://127.0.0.1:7860/audio/{data['audio_file']}"
                st.audio(audio_url, format="audio/mp3")

        else:
            st.error(f"API Error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        st.error(f"Request Failed: {e}")

else:
    st.info("Please enter a company name to fetch news.")

