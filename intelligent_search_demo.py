#!/usr/bin/env python3
"""
Intelligent Semantic Search Demo for Auto/Trailer Parts

Dependencies:
    pip install sentence-transformers torch

Usage:
    python intelligent_search_demo.py
"""
from sentence_transformers import SentenceTransformer, util

# Step 2: Sample parts catalog (expand as needed)
parts_catalog = [
    "2018 Ford F-150 brake light",
    "Trailer hitch for Toyota Tacoma",
    "LED tail lamp for semi-trailer",
    "Truck tire 295/80R22.5",
    "12V battery for Mahindra Bolero",
    "Maruti Suzuki Swift headlight assembly",
    "Ashok Leyland truck clutch plate",
    "Tata Ace mini truck rear view mirror",
    "Eicher Pro 3015 air filter",
    "Scania R500 cabin air spring",
    "Volvo FH16 engine oil filter",
    "Isuzu D-Max fuel injector",
    "Mahindra Blazo cabin shock absorber",
    "BharatBenz 1217 tail light lens",
    "Force Traveller alternator belt",
    "Piaggio Ape Xtra front fork",
    "Leyland Dost brake pad set",
    "Tata Prima 4038 windshield wiper blade",
    "Truck mudguard universal",
    "Trailer king pin 2 inch",
    # ... add more as needed
]

# Step 1: Semantic search setup
model = SentenceTransformer('all-MiniLM-L6-v2')
catalog_embeddings = model.encode(parts_catalog, convert_to_tensor=True)

def find_best_part(user_query):
    query_embedding = model.encode(user_query, convert_to_tensor=True)
    scores = util.pytorch_cos_sim(query_embedding, catalog_embeddings)[0]
    best_idx = scores.argmax().item()
    return parts_catalog[best_idx], float(scores[best_idx])

if __name__ == "__main__":
    print("Intelligent Part Search Demo\nType a description of the part you need (or 'exit' to quit):")
    while True:
        user_input = input("Describe the part: ").strip()
        if not user_input or user_input.lower() == 'exit':
            print("Exiting.")
            break
        best_part, score = find_best_part(user_input)
        print(f"Best match: {best_part}\n(Similarity score: {score:.2f})\n") 