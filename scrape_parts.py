#!/usr/bin/env python3
import time
import json
import base64
import urllib.parse
from typing import Dict, List, Optional
import re
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ChromaDB and Sentence Transformers
import chromadb
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AmazonInSeleniumScraper:
    """Enhanced Amazon.in scraper with better error handling and data extraction."""
    
    def __init__(self, headless: bool = True, timeout: int = 15):
        self.timeout = timeout
        chrome_opts = Options()
        if headless:
            chrome_opts.add_argument("--headless")
        chrome_opts.add_argument("--disable-gpu")
        chrome_opts.add_argument("--window-size=1920,1080")
        chrome_opts.add_argument("--lang=en-IN")
        chrome_opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_opts.add_experimental_option("useAutomationExtension", False)
        chrome_opts.add_argument("--disable-blink-features=AutomationControlled")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_opts)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def scrape(self, query: str, max_results: int = 10) -> Dict:
        """Scrape Amazon.in for trailer parts with enhanced error handling."""
        base = "https://www.amazon.in"
        search_url = f"{base}/s?k={urllib.parse.quote(query)}&ref=sr_pg_1"
        
        logger.info(f"Searching Amazon.in: {search_url}")
        
        try:
            self.driver.get(search_url)
            time.sleep(3)  # Wait for page load
            
            # Handle potential CAPTCHA or robot detection
            if "robot" in self.driver.page_source.lower() or "captcha" in self.driver.page_source.lower():
                logger.warning("Potential CAPTCHA detected. Waiting longer...")
                time.sleep(10)
            
            # Try multiple selectors for search results
            selectors_to_try = [
                "div[data-component-type='s-search-result']",
                "div.s-result-item",
                "div[data-asin]",
                ".s-search-result",
                "[data-cy='title-recipe-label']"
            ]
            
            items = []
            for selector in selectors_to_try:
                try:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    items = soup.select(selector)
                    if items:
                        logger.info(f"Found {len(items)} items using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not items:
                # Fallback: get all divs with data-asin attribute
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                items = soup.find_all('div', {'data-asin': True})
                logger.info(f"Fallback: Found {len(items)} items with data-asin")
            
            products = self._extract_products(items, base, max_results)
            
            return {
                "website": "amazon.in",
                "search_url": search_url,
                "products": products,
                "total_found": len(items),
                "successfully_extracted": len(products)
            }
            
        except Exception as e:
            logger.error(f"Error during Amazon scraping: {e}")
            return {
                "website": "amazon.in",
                "search_url": search_url,
                "products": [],
                "error": str(e)
            }
    
    def _extract_products(self, items: List, base_url: str, max_results: int) -> List[Dict]:
        """Extract product data with improved parsing."""
        products = []
        
        for i, prod in enumerate(items[:max_results * 2]):  # Get more items to filter
            try:
                # Skip if no data-asin or empty asin
                asin = prod.get('data-asin', '')
                if not asin or len(asin) < 5:
                    continue
                
                product_data = self._extract_product_data(prod, base_url)
                if product_data and self._is_valid_product(product_data):
                    products.append(product_data)
                    logger.debug(f"Successfully extracted: {product_data['name'][:50]}...")
                    if len(products) >= max_results:
                        break
                        
            except Exception as e:
                logger.debug(f"Error processing item {i}: {e}")
                continue
        
        return products
    
    def _is_valid_product(self, product: Dict) -> bool:
        """Validate if product data is complete enough."""
        return (
            product.get('name') and 
            len(product['name']) > 10 and
            product.get('url') and
            'amazon.in' in product['url']
        )
    
    def _extract_product_data(self, prod, base_url) -> Optional[Dict]:
        """Extract product data with improved selectors."""
        
        # Title and URL extraction with better selectors
        title, url = self._extract_title_and_url(prod, base_url)
        if not title or not url:
            return None
        
        # Price extraction with enhanced parsing
        price = self._extract_price(prod)
        
        # Rating extraction
        rating = self._extract_rating(prod)
        
        # Prime availability
        prime = bool(prod.select_one("i[aria-label*='Prime'], .a-icon-prime, [aria-label*='prime']"))
        
        # Image URL
        image_url = self._extract_image_url(prod)
        
        # Availability status
        availability = self._extract_availability(prod)
        
        # Additional metadata
        review_count = self._extract_review_count(prod)
        
        return {
            "name": title,
            "url": url,
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "prime": prime,
            "image_url": image_url,
            "availability": availability,
            "asin": prod.get('data-asin', '')
        }
    
    def _extract_title_and_url(self, prod, base_url) -> tuple:
        """Extract title and URL with multiple fallback methods."""
        title_selectors = [
            "h2 a span",
            "h2 a",
            "[data-cy='title-recipe-label']",
            "h2 span",
            ".s-link-style a",
            "a .a-link-normal",
            "a[href*='/dp/']",
            ".a-link-normal"
        ]
        
        for selector in title_selectors:
            title_elem = prod.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 10:
                    # Find the parent link or the element itself if it's a link
                    if title_elem.name == 'a' and title_elem.get('href'):
                        url = urllib.parse.urljoin(base_url, title_elem['href'])
                    else:
                        link_elem = title_elem.find_parent('a')
                        if link_elem and link_elem.get('href'):
                            url = urllib.parse.urljoin(base_url, link_elem['href'])
                        else:
                            continue
                    
                    if url:
                        return title, url
        
        return None, None
    
    def _extract_price(self, prod) -> Optional[str]:
        """Extract price with multiple parsing methods."""
        price_selectors = [
            ".a-price .a-offscreen",
            ".a-price .a-price-whole",
            ".a-price-symbol + .a-price-whole",
            "[data-a-color='price'] .a-offscreen",
            ".a-price-range .a-offscreen",
            ".a-color-price",
            ".a-price"
        ]
        
        for selector in price_selectors:
            price_elem = prod.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                if price_text and ('₹' in price_text or ',' in price_text or price_text.replace('.', '').replace(',', '').isdigit()):
                    # Clean up the price
                    if 'offscreen' in price_elem.get('class', []):
                        return price_text
                    else:
                        return price_text if '₹' in price_text else f"₹{price_text}"
        
        # Try to construct from whole and fraction parts
        whole_elem = prod.select_one(".a-price-whole")
        if whole_elem:
            whole_text = whole_elem.get_text(strip=True).replace(',', '')
            frac_elem = prod.select_one(".a-price-fraction")
            if frac_elem:
                frac_text = frac_elem.get_text(strip=True)
                return f"₹{whole_text}.{frac_text}"
            else:
                return f"₹{whole_text}"
        
        return None
    
    def _extract_rating(self, prod) -> Optional[str]:
        """Extract rating with better parsing."""
        rating_selectors = [
            ".a-icon-alt",
            "[aria-label*='out of']",
            ".a-star-mini .a-icon-alt"
        ]
        
        for selector in rating_selectors:
            rating_elem = prod.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get('aria-label', '') or rating_elem.get_text(strip=True)
                if 'out of' in rating_text:
                    rating_match = re.search(r'(\d+\.?\d*)\s*out of', rating_text)
                    if rating_match:
                        return rating_match.group(1)
        
        return None
    
    def _extract_review_count(self, prod) -> Optional[str]:
        """Extract number of reviews."""
        review_selectors = [
            "[aria-label*='rating']",
            ".a-link-normal:contains('(')"
        ]
        
        for selector in review_selectors:
            review_elem = prod.select_one(selector)
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                review_match = re.search(r'\((\d+(?:,\d+)*)\)', review_text)
                if review_match:
                    return review_match.group(1)
        
        return None
    
    def _extract_image_url(self, prod) -> Optional[str]:
        """Extract product image URL."""
        img_elem = prod.select_one("img.s-image")
        if img_elem:
            return img_elem.get('src') or img_elem.get('data-src')
        return None
    
    def _extract_availability(self, prod) -> str:
        """Extract availability status."""
        unavailable_indicators = [
            ".a-color-price",
            "[data-a-color='secondary']"
        ]
        
        for selector in unavailable_indicators:
            avail_elem = prod.select_one(selector)
            if avail_elem:
                avail_text = avail_elem.get_text(strip=True).lower()
                if any(word in avail_text for word in ['unavailable', 'out of stock', 'temporarily']):
                    return avail_text.title()
        
        return "In Stock"

    def close(self):
        """Close the webdriver."""
        try:
            self.driver.quit()
        except Exception as e:
            logger.error(f"Error closing driver: {e}")


class VectorDBManager:
    """Manages vector database operations with ChromaDB."""
    
    def __init__(self, path: str = "parts_db"):
        self.client = chromadb.PersistentClient(path=path)
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.collection = self.client.get_or_create_collection(
            name="trailer_parts",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"ChromaDB collection 'trailer_parts' loaded/created at path: {path}")

    def upsert_products(self, products: List[Dict], source: str):
        """Generate embeddings and upsert products into ChromaDB."""
        if not products:
            return

        ids = []
        documents = []
        metadatas = []

        for prod in products:
            # Create a unique ID for each product
            item_id = prod.get('item_id') or prod.get('asin')
            if not item_id:
                logger.warning(f"Skipping product without a unique ID: {prod['name']}")
                continue
            
            unique_id = f"{source}_{item_id}"
            
            # Text to be embedded
            doc_text = f"Name: {prod['name']} Price: {prod.get('price', 'N/A')}"
            
            # All other data as metadata
            metadata = {key: str(value) for key, value in prod.items() if value is not None}
            metadata['source'] = source

            ids.append(unique_id)
            documents.append(doc_text)
            metadatas.append(metadata)

        if not ids:
            return

        # Generate embeddings in a batch
        embeddings = self.model.encode(documents).tolist()
        
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Upserted {len(ids)} products from {source} into ChromaDB.")

class EbayScraper:
    """Enhanced eBay scraper with better error handling."""
    
    def __init__(self, client_id: str, client_secret: str, use_sandbox: bool = False):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.client_id = client_id
        self.client_secret = client_secret
        
        if use_sandbox:
            self.oauth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            self.search_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
        else:
            self.oauth_url = "https://api.ebay.com/identity/v1/oauth2/token"
            self.search_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        
        self._token = None
        self._token_expires = 0

    def _get_token(self) -> str:
        """Get OAuth token with better error handling."""
        if self._token and time.time() < self._token_expires - 60:
            return self._token

        try:
            creds = f"{self.client_id}:{self.client_secret}"
            headers = {
                "Authorization": "Basic " + base64.b64encode(creds.encode()).decode(),
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }
            
            resp = self.session.post(self.oauth_url, headers=headers, data=data, timeout=10)
            resp.raise_for_status()
            
            tok = resp.json()
            self._token = tok["access_token"]
            self._token_expires = time.time() + int(tok["expires_in"])
            
            logger.info("Successfully obtained eBay access token")
            return self._token
            
        except Exception as e:
            logger.error(f"Error getting eBay token: {e}")
            raise

    def scrape(self, query: str, max_results: int = 10) -> Dict:
        """Scrape eBay with enhanced filtering and error handling."""
        try:
            token = self._get_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            # Enhanced search parameters
            params = {
                "q": query,
                "limit": max_results,
                "sort": "price",  # Sort by price for better results
                "fieldgroups": "MATCHING_ITEMS,FULL"  # Get more detailed info
            }
            
            resp = self.session.get(self.search_url, headers=headers, params=params, timeout=15)
            search_url = resp.url

            if resp.status_code != 200:
                logger.error(f"eBay API returned status {resp.status_code}")
                return {
                    "website": "ebay.com", 
                    "search_url": search_url, 
                    "products": [], 
                    "error": f"HTTP {resp.status_code}"
                }

            data = resp.json()
            items = data.get("itemSummaries", [])
            products = []
            
            for item in items:
                product = self._extract_ebay_product(item)
                if product:
                    products.append(product)

            logger.info(f"Successfully scraped {len(products)} products from eBay")
            
            return {
                "website": "ebay.com", 
                "search_url": search_url, 
                "products": products,
                "total_found": data.get("total", len(items))
            }
            
        except Exception as e:
            logger.error(f"Error during eBay scraping: {e}")
            return {
                "website": "ebay.com",
                "search_url": "",
                "products": [],
                "error": str(e)
            }
    
    def _extract_ebay_product(self, item: Dict) -> Optional[Dict]:
        """Extract eBay product data with enhanced fields."""
        try:
            product = {
                "name": item.get("title"),
                "url": item.get("itemWebUrl"),
                "item_id": item.get("itemId")
            }
            
            # Price handling
            if item.get("price"):
                product["price"] = f"{item['price']['value']} {item['price']['currency']}"
            
            # Shipping info
            if item.get("shippingOptions"):
                shipping = item["shippingOptions"][0]
                if shipping.get("shippingCost"):
                    product["shipping_cost"] = f"{shipping['shippingCost']['value']} {shipping['shippingCost']['currency']}"
                else:
                    product["shipping_cost"] = "Free"
            
            # Additional details
            if item.get("condition"):
                product["condition"] = item["condition"]
            
            if item.get("seller"):
                seller_info = item["seller"]
                product["seller"] = seller_info.get("username")
                if seller_info.get("feedbackPercentage"):
                    product["seller_rating"] = f"{seller_info['feedbackPercentage']}%"
            
            # Image
            if item.get("image"):
                product["image_url"] = item["image"]["imageUrl"]
            
            # Location
            if item.get("itemLocation"):
                product["location"] = item["itemLocation"].get("country")
            
            return product
            
        except Exception as e:
            logger.debug(f"Error extracting eBay product: {e}")
            return None


def save_results(results: Dict, query: str) -> str:
    """Save results to JSON file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trailer_parts_{query.replace(' ', '_').replace('/', '_')}_{timestamp}.json"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return ""


def display_results(results: Dict):
    """Display results in a formatted way."""
    print("\n" + "="*80)
    print("TRAILER PARTS SEARCH RESULTS")
    print("="*80)
    print(f"Search Term: {results['search_term']}")
    print(f"Timestamp: {results['timestamp']}")
    
    for source in results['sources']:
        website = source['website'].upper()
        products = source['products']
        total_found = source.get('total_found', len(products))
        
        print(f"\n{website} - Found {len(products)} products (Total available: {total_found}):")
        print("-" * 60)
        
        if source.get('error'):
            print(f"❌ Error: {source['error']}")
            continue
        
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product['name'][:80]}{'...' if len(product['name']) > 80 else ''}")
            
            if product.get('price'):
                print(f"   💰 Price: {product['price']}")
            
            if product.get('rating'):
                stars = "⭐" * int(float(product['rating']))
                print(f"   {stars} Rating: {product['rating']}/5")
                if product.get('review_count'):
                    print(f"   👥 Reviews: {product['review_count']}")
            
            if product.get('condition'):
                print(f"   📦 Condition: {product['condition']}")
            
            if product.get('prime'):
                print("   🚚 Prime: Available")
            
            if product.get('shipping_cost'):
                print(f"   🚛 Shipping: {product['shipping_cost']}")
            
            if product.get('seller'):
                seller_info = f"👤 Seller: {product['seller']}"
                if product.get('seller_rating'):
                    seller_info += f" ({product['seller_rating']})"
                print(f"   {seller_info}")
            
            print(f"   🔗 URL: {product.get('url', 'N/A')}")


def main():
    """Main function with enhanced error handling and user experience."""
    # eBay credentials - replace with your own
    EBAY_CLIENT_ID = your client id
    EBAY_CLIENT_SECRET = your client secret key

    print("🚛 Trailer Parts Scraper v2.0")
    print("=" * 40)
    
    # Get search query
    query = input("Enter trailer part name to search: ").strip()
    if not query:
        print("❌ Please enter a valid search term.")
        return
    
    # Get number of results
    try:
        max_results = int(input("Number of results per site (default 10): ").strip() or "10")
        max_results = min(max_results, 50)  # Limit to 50 for performance
    except ValueError:
        max_results = 10
    
    print(f"\n🔍 Searching for: '{query}' (max {max_results} results per site)")
    print("This may take a few minutes...\n")
    
    # Initialize scrapers
    amazon_scraper = None
    ebay_scraper = None
    
    try:
        print("🏪 Initializing Amazon scraper...")
        amazon_scraper = AmazonInSeleniumScraper()
        
        print("🛒 Initializing eBay scraper...")
        ebay_scraper = EbayScraper(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, use_sandbox=False)

        print("🗂️  Initializing Vector DB...")
        db_manager = VectorDBManager()
        
        # Scrape Amazon
        print("🔍 Scraping Amazon.in...")
        amazon_results = amazon_scraper.scrape(query, max_results=max_results)
        db_manager.upsert_products(amazon_results['products'], 'amazon.in')
        
        # Scrape eBay
        print("🔍 Scraping eBay...")
        ebay_results = ebay_scraper.scrape(query, max_results=max_results)
        db_manager.upsert_products(ebay_results['products'], 'ebay.com')
        
        # Compile results
        results = {
            "search_term": query,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "max_results_requested": max_results,
            "sources": [amazon_results, ebay_results]
        }
        
        # Display results
        display_results(results)
        
        # Save results
        filename = save_results(results, query)
        if filename:
            print(f"\n💾 Results saved to: {filename}")
        
        # Summary
        total_products = sum(len(source['products']) for source in results['sources'])
        print(f"\n✅ Search completed! Found {total_products} products total.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Search interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ An error occurred: {e}")
    finally:
        # Clean up
        if amazon_scraper:
            print("🧹 Closing Amazon scraper...")
            amazon_scraper.close()


if __name__ == "__main__":
    main()
