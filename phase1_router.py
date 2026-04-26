# Phase 1: Vector-Based Persona Matching
# This file embeds bot personas and routes posts to matching bots

import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load API key from .env file
load_dotenv()

# Load embedding model (runs locally, no API needed)
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3 Bot Personas from the assignment
bots = {
    "Bot_A": "I believe AI and crypto will solve all human problems. I am highly optimistic about technology, Elon Musk, and space exploration. I dismiss regulatory concerns.",
    "Bot_B": "I believe late-stage capitalism and tech monopolies are destroying society. I am highly critical of AI, social media, and billionaires. I value privacy and nature.",
    "Bot_C": "I strictly care about markets, interest rates, trading algorithms, and making money. I speak in finance jargon and view everything through the lens of ROI."
}

# Generate embeddings for each persona
bot_names = list(bots.keys())
bot_texts = list(bots.values())
bot_embeddings = model.encode(bot_texts, normalize_embeddings=True)

# Store embeddings in FAISS vector store
dimension = bot_embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # Inner Product = Cosine Similarity (since normalized)
index.add(np.array(bot_embeddings))

print("✅ Bot personas embedded and stored in FAISS!")

def route_post_to_bots(post_content: str, threshold: float = 0.2):
    # Embed the incoming post
    post_embedding = model.encode([post_content], normalize_embeddings=True)
    
    # Search FAISS for similar bots
    similarities, indices = index.search(np.array(post_embedding), k=3)
    
    matched_bots = []
    for sim, idx in zip(similarities[0], indices[0]):
        if sim >= threshold:
            matched_bots.append({
                "bot": bot_names[idx],
                "similarity": round(float(sim), 4)
            })
    
    return matched_bots

# Test with multiple posts
if __name__ == "__main__":
    test_posts = [
        "OpenAI just released a new model that might replace junior developers.",
        "Bitcoin hits new all-time high amid regulatory ETF approvals.",
        "Big tech companies are destroying democracy and privacy."
    ]
    
    for post in test_posts:
        print(f"\n📨 Post: {post}")
        results = route_post_to_bots(post)
        
        if results:
            print("🤖 Matched Bots:")
            for r in results:
                print(f"  - {r['bot']} (similarity: {r['similarity']})")
        else:
            print("❌ No bots matched!")