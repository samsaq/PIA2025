import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import dotenv
import os
import psycopg2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
dotenv.load_dotenv()

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Database connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Function to establish database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to extract text from a webpage
def extract_text_from_webpage(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        for element in soup.select('nav, footer, header, aside, script, style'):
            element.decompose()
        
        main_content = soup.select_one('main, article, [role="main"], .content, #content')
        content = main_content if main_content else soup.body
        text_elements = content.select("p, h1, h2, h3, h4, h5, h6, li, blockquote")
        text = " ".join([elem.get_text().strip() for elem in text_elements if elem.get_text().strip()])
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

# Function to analyze webpage trustworthiness using GPT
def analyze_webpage_with_gpt(text):
    try:
        if not text or len(text) < 100:
            return "Error: The extracted text is too short for analysis."

        prompt = f"Evaluate the following webpage for factual accuracy and trustworthiness: {text[:4000]}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a fact-checking assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error communicating with GPT: {e}"

# Retrieve verified documents from the database
def get_verified_documents():
    conn = get_db_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM verification_table WHERE content IS NOT NULL')
    documents = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return documents

# Compute similarity and retrieve top 5 matches
def compute_similarity(webpage_text, verified_docs, k=5):
    if not verified_docs:  # If the list is empty
        return []     # Return empty list for no matches
    
    vectorizer = TfidfVectorizer()
    all_texts = [webpage_text] + verified_docs
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    # Make sure k isn't larger than the number of documents
    k = min(k, len(verified_docs))
    
    top_k_indices = similarities.argsort()[-k:][::-1]
    top_k_similarities = [(verified_docs[i], similarities[i]) for i in top_k_indices]
    
    return top_k_similarities

# Function to check congruency with trusted documents using GPT
def verify_with_trusted_docs(webpage_text, trusted_docs):
    try:
        prompt = f"Given the following trusted documents:\n{trusted_docs}\n\nDoes this new document align with them? {webpage_text[:4000]}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a fact-checking assistant ensuring document congruency."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error communicating with GPT: {e}"

@app.route("/api/query", methods=["POST"])
def query_rag():
    try:
        data = request.json
        url = data.get("url")
        
        # Step 1: Extract webpage content
        webpage_text = extract_text_from_webpage(url)
        if "Error" in webpage_text:
            return jsonify({"error": webpage_text}), 500
        
        # Step 2: Analyze trustworthiness with GPT
        gpt_analysis = analyze_webpage_with_gpt(webpage_text)
        if "Error" in gpt_analysis:
            return jsonify({"error": gpt_analysis}), 500
        
        # Step 3: Retrieve verified documents and check similarity
        verified_docs = get_verified_documents()
        top_matches = compute_similarity(webpage_text, verified_docs)
        
        # Step 4: Verify congruency with GPT using top similar documents
        trusted_docs = [doc for doc, _ in top_matches]
        congruency_analysis = verify_with_trusted_docs(webpage_text, trusted_docs)
        
        similarity_check_passed = all(sim >= 0.7 for _, sim in top_matches)
        #if similarity check is empty, then skip over the congruency check
        if similarity_check_passed:
            congruency_check_passed = "consistent" in congruency_analysis.lower()
        else:
            congruency_check_passed = True
            similarity_check_passed = True
        
        if similarity_check_passed and congruency_check_passed:
            result = {
                "output": {
                    "Analysis": "Trusted",
                    "GPT_Analysis": gpt_analysis
                },
                "content": webpage_text
            }
        else:
            result = {
                "output": {
                    "Analysis": "Untrusted",
                    "GPT_Analysis": gpt_analysis
                },
                "content": webpage_text
            }
        
        # Store result as JSON
        with open("verification_result.json", "w") as f:
            json.dump(result, f, indent=4)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})
