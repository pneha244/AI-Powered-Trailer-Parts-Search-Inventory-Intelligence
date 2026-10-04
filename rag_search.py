import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set your Gemini API key directly in code (for local testing only)
genai.configure(api_key="your key")

class RAGSearch:
    def __init__(self, db_path="parts_db", collection_name="trailer_parts", top_k=20):
        self.client = chromadb.PersistentClient(path=db_path)
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.collection = self.client.get_collection(name=collection_name)
        self.top_k = top_k

    def retrieve(self, query):
        logger.info(f"Retrieving top {self.top_k} products for query: {query}")
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.top_k,
            include=["metadatas", "documents", "distances"]
        )
        return results

    def format_context(self, results):
        metadatas = results["metadatas"][0]
        context = ""
        for i, meta in enumerate(metadatas):
            context += f"{i+1}. Name: {meta.get('name', 'N/A')}, Price: {meta.get('price', 'N/A')}, Source: {meta.get('source', 'N/A')}, URL: {meta.get('url', 'N/A')}\n"
        return context

    def ask_llm(self, user_query, context):
        prompt = f"""
You are an expert assistant for trailer parts. A user is searching for a part with the following query:
"{user_query}"

Here are the top {self.top_k} most relevant products from the database:
{context}

Based on the query and the context, recommend the single best product for the user to buy. For your answer, provide:
- The product name
- The price
- The source (Amazon/eBay)
- The direct URL for purchase
- A short reason for your recommendation

If none of the products are a good match, say so politely.
"""
        logger.info("Sending prompt to Gemini LLM...")
        try:
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            # Print available models for debugging
            try:
                print("\nAvailable Gemini models:")
                print([m.name for m in genai.list_models()])
            except Exception as e2:
                print(f"Could not list models: {e2}")
            return "[Gemini LLM error: see logs above]"

    def rag_search(self, user_query):
        results = self.retrieve(user_query)
        context = self.format_context(results)
        answer = self.ask_llm(user_query, context)
        print("\n===== RAG Recommendation =====\n")
        print(answer)
        print("\n============================\n")

def main():
    print("\n🧠 Trailer Parts RAG Search (Gemini)")
    print("=" * 40)
    print("Type 'exit' or 'quit' to stop.")
    rag = RAGSearch()
    while True:
        try:
            query = input("\nSearch for a part > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                print("👋 Exiting RAG search. Goodbye!")
                break
            rag.rag_search(query)
        except KeyboardInterrupt:
            print("\n👋 Exiting RAG search. Goodbye!")
            break
        except Exception as e:
            logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 
