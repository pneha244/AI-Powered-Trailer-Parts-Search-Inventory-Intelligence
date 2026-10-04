import chromadb
from sentence_transformers import SentenceTransformer
import logging

# Set up logging to suppress noisy output and show important info
logging.basicConfig(level=logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class IntelligentSearch:
    """Handles vector search operations on the parts database."""

    def __init__(self, db_path: str = "parts_db", collection_name: str = "trailer_parts"):
        """
        Initializes the search client, embedding model, and connects to the ChromaDB collection.
        """
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.model = SentenceTransformer('all-mpnet-base-v2')
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Successfully connected to ChromaDB collection '{collection_name}'.")
            logger.info(f"Total items in DB: {self.collection.count()}")
        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {e}")
            logger.error("Did you run the 'scrape_parts.py' script first to create and populate the database?")
            self.collection = None

    def search(self, query: str, top_n: int = 5):
        """
        Performs a semantic search on the vector database.

        Args:
            query (str): The user's search query.
            top_n (int): The number of top results to return.
        """
        if not self.collection:
            logger.error("Search cannot proceed, collection not available.")
            return

        logger.info(f"Encoding query: '{query}'")
        query_embedding = self.model.encode(query).tolist()

        logger.info(f"Searching for top {top_n} results...")
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_n,
            include=["metadatas", "documents", "distances"]
        )
        
        self._display_results(results)

    def _display_results(self, results: dict):
        """Formats and prints the search results."""
        if not results or not results.get('ids', [[]])[0]:
            print("\n❌ No results found for your query.")
            return

        print("\n" + "="*80)
        print("🔍 INTELLIGENT SEARCH RESULTS")
        print("="*80)

        ids = results['ids'][0]
        distances = results['distances'][0]
        metadatas = results['metadatas'][0]

        for i, (id, dist, meta) in enumerate(zip(ids, distances, metadatas)):
            similarity = 1 - dist  # Convert distance to similarity score
            
            print(f"\n{i+1}. {meta.get('name', 'N/A')}")
            print(f"   ✨ Similarity: {similarity:.2f}")
            print(f"   💰 Price: {meta.get('price', 'N/A')}")
            print(f"   🌐 Source: {meta.get('source', 'N/A')}")
            print(f"   🔗 URL: {meta.get('url', 'N/A')}")
        print("\n" + "="*80)


def main():
    """Main function to run the intelligent search application."""
    print("🧠 Trailer Parts Intelligent Search")
    print("=" * 40)
    print("Enter a search query to find similar parts in the database.")
    print("Type 'exit' or 'quit' to stop.")
    
    search_app = IntelligentSearch()
    if not search_app.collection:
        return

    while True:
        try:
            query = input("\nSearch for a part > ").strip()
            if not query:
                continue
            if query.lower() in ['exit', 'quit']:
                print("👋 Exiting search. Goodbye!")
                break
            
            search_app.search(query)
            
        except KeyboardInterrupt:
            print("\n👋 Exiting search. Goodbye!")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main() 