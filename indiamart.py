import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import quote_plus, urljoin
import pandas as pd
from typing import List, Dict, Optional
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

class IndiaMartScraper:
    def __init__(self, use_selenium=True):
        self.base_url = "https://www.indiamart.com"
        self.use_selenium = use_selenium
        self.driver = None
        
        if use_selenium:
            self._setup_selenium()
        else:
            self._setup_requests()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("Selenium WebDriver initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Selenium: {e}")
            print("Falling back to requests method")
            self.use_selenium = False
            self._setup_requests()
    
    def _setup_requests(self):
        """Setup requests session"""
        self.session = requests.Session()
        
        # Enhanced headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Referer': 'https://www.google.com/'
        }
        self.session.headers.update(self.headers)
    
    def search_parts(self, part_name: str, max_results: int = 20) -> List[Dict]:
        """
        Search for parts on IndiaMART using updated methods
        """
        print(f"Searching for: {part_name}")
        
        if self.use_selenium:
            return self._search_with_selenium(part_name, max_results)
        else:
            return self._search_with_requests(part_name, max_results)
    
    def _search_with_selenium(self, part_name: str, max_results: int) -> List[Dict]:
        """
        Search using Selenium WebDriver
        """
        try:
            # Navigate to IndiaMART
            print("Navigating to IndiaMART...")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Find search box and enter search term
            search_selectors = [
                'input[name="ss"]',
                'input[placeholder*="search"]',
                'input[type="search"]',
                '#search',
                '.search-input',
                'input[class*="search"]'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not search_box:
                print("Could not find search box")
                return []
            
            # Enter search term and submit
            search_box.clear()
            search_box.send_keys(part_name)
            time.sleep(1)
            
            # Find and click search button
            search_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                '.search-btn',
                'button[class*="search"]',
                '.btn-search'
            ]
            
            for selector in search_button_selectors:
                try:
                    search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    search_button.click()
                    break
                except NoSuchElementException:
                    continue
            
            # Wait for results to load
            time.sleep(5)
            
            # Extract product data
            return self._extract_selenium_results(max_results)
            
        except Exception as e:
            print(f"Selenium search failed: {e}")
            return []
    
    def _extract_selenium_results(self, max_results: int) -> List[Dict]:
        """
        Extract product results using Selenium
        """
        products = []
        
        # Save page source for debugging
        with open('debug_selenium.html', 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        
        # Multiple selectors for product containers
        product_selectors = [
            '[data-testid*="product"]',
            '.product-card',
            '.search-card',
            '.listing-card',
            '.prd',
            '.product-item',
            '.lst',
            '.item',
            '.result-item',
            'div[class*="product"]',
            'div[class*="card"]'
        ]
        
        product_elements = []
        for selector in product_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 3:  # Need reasonable number
                    product_elements = elements
                    print(f"Found {len(elements)} products with selector: {selector}")
                    break
            except Exception as e:
                continue
        
        if not product_elements:
            print("No product elements found with Selenium")
            return []
        
        # Extract product information
        for i, element in enumerate(product_elements[:max_results]):
            try:
                product_data = self._parse_selenium_element(element)
                if product_data:
                    products.append(product_data)
                    print(f"Extracted product {i+1}: {product_data.get('name', 'Unknown')}")
                
            except Exception as e:
                print(f"Error extracting product {i+1}: {e}")
                continue
        
        return products
    
    def _parse_selenium_element(self, element) -> Optional[Dict]:
        """
        Parse product element using Selenium
        """
        try:
            product_data = {}
            
            # Extract product name and URL
            try:
                link_element = element.find_element(By.CSS_SELECTOR, 'a')
                product_data['name'] = link_element.get_attribute('title') or link_element.text.strip()
                product_data['url'] = link_element.get_attribute('href')
            except:
                product_data['name'] = element.text.strip()[:100]
                product_data['url'] = 'N/A'
            
            # Extract price
            price_selectors = [
                '.price', '.prd-price', '.lst-price', '.product-price',
                '[class*="price"]', '[class*="cost"]', '[class*="rate"]',
                '.getquote', 'p.getquote', 'p.price', 'p.getquote',
            ]
            
            for selector in price_selectors:
                try:
                    price_element = element.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text.strip()
                    if price_text:
                        product_data['price'] = price_text
                        break
                except:
                    continue
            
            # Fallback for 'Ask Price'
            if 'price' not in product_data:
                try:
                    ask_price_elem = element.find(string=lambda t: t and 'Ask Price' in t)
                    if ask_price_elem:
                        product_data['price'] = ask_price_elem.strip()
                except:
                    pass
            
            # Extract company
            company_selectors = [
                '.companyname a', '.company-name', '.prd-comp-name', '.lst-comp-name',
                '.seller-name', '[class*="company"]', '[class*="seller"]', '[class*="supplier"]'
            ]
            
            for selector in company_selectors:
                try:
                    company_element = element.find_element(By.CSS_SELECTOR, selector)
                    company_text = company_element.text.strip()
                    if company_text:
                        product_data['company'] = company_text
                        break
                except:
                    continue
            
            # Extract location
            location_selectors = [
                '.newLocationUi span.elps', '.location', '.prd-comp-loc', '.lst-comp-loc',
                '[class*="location"]', '[class*="city"]', '[class*="address"]'
            ]
            
            for selector in location_selectors:
                try:
                    location_element = element.find_element(By.CSS_SELECTOR, selector)
                    location_text = location_element.text.strip()
                    if location_text:
                        product_data['location'] = location_text
                        break
                except:
                    continue
            
            # Set defaults
            product_data.setdefault('price', 'N/A')
            product_data.setdefault('company', 'N/A')
            product_data.setdefault('location', 'N/A')
            
            return product_data if product_data.get('name') else None
            
        except Exception as e:
            print(f"Error parsing Selenium element: {e}")
            return None
    
    def _search_with_requests(self, part_name: str, max_results: int) -> List[Dict]:
        """
        Updated search using requests with better URL patterns
        """
        try:
            # Updated search URLs based on current IndiaMART structure
            search_urls = [
                # Try direct search
                f"{self.base_url}/search.mp?ss={quote_plus(part_name)}",
                f"{self.base_url}/search?ss={quote_plus(part_name)}",
                # Try category-based search
                f"{self.base_url}/impcat/{quote_plus(part_name.replace(' ', '-'))}.html",
                # Try city-based search
                f"{self.base_url}/city/{quote_plus(part_name.replace(' ', '-'))}.html",
                # Try alternative formats
                f"{self.base_url}/proddetail/{quote_plus(part_name.replace(' ', '-'))}",
                f"{self.base_url}/supplier/{quote_plus(part_name.replace(' ', '-'))}",
            ]
            
            for i, url in enumerate(search_urls):
                print(f"Trying URL {i+1}: {url}")
                try:
                    # Add random delay
                    time.sleep(random.uniform(2, 4))
                    
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        print(f"Success with URL {i+1}")
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Save for debugging
                        with open(f'debug_response_{i+1}.html', 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        
                        products = self._extract_products_updated(soup, max_results)
                        if products:
                            return products
                    else:
                        print(f"URL {i+1} failed with status: {response.status_code}")
                        
                except Exception as e:
                    print(f"Error with URL {i+1}: {e}")
                    continue
            
            # If direct search fails, try alternative approach
            return self._alternative_search_approach(part_name, max_results)
            
        except Exception as e:
            print(f"Requests search failed: {e}")
            return []
    
    def _extract_products_updated(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """
        Updated product extraction with better selectors
        """
        products = []
        
        # Enhanced product selectors
        product_selectors = [
            # Modern React-based selectors
            '[data-testid*="product"]',
            '[data-cy*="product"]',
            '[data-track*="product"]',
            
            # Card-based selectors
            '.product-card',
            '.search-card',
            '.listing-card',
            '.result-card',
            
            # Traditional selectors
            '.prd',
            '.product-item',
            '.lst',
            '.listing-item',
            '.search-item',
            
            # Generic container selectors
            'div[class*="product"]',
            'div[class*="listing"]',
            'div[class*="result"]',
            'div[class*="item"]',
            
            # Link-based extraction
            'a[href*="proddetail"]',
            'a[href*="product"]'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 2:
                product_elements = elements
                print(f"Found {len(elements)} elements with selector: {selector}")
                break
        
        if not product_elements:
            print("No product elements found, trying alternative extraction...")
            return self._extract_from_all_links(soup, max_results)
        
        # Extract product data
        for i, element in enumerate(product_elements[:max_results]):
            try:
                product_data = self._parse_product_element_updated(element)
                if product_data and product_data.get('name'):
                    products.append(product_data)
                    print(f"Extracted: {product_data['name'][:50]}...")
                    
            except Exception as e:
                print(f"Error extracting product {i+1}: {e}")
                continue
        
        return products
    
    def _parse_product_element_updated(self, element) -> Optional[Dict]:
        """
        Updated product element parsing
        """
        try:
            product_data = {}
            
            # Extract name and URL
            link_selectors = [
                'a[href*="proddetail"]',
                'a[href*="product"]',
                'a[title]',
                'h2 a', 'h3 a', 'h4 a',
                '.product-name a',
                '.listing-name a',
                'a'
            ]
            
            for selector in link_selectors:
                link = element.select_one(selector)
                if link:
                    product_data['name'] = link.get('title') or link.get_text(strip=True)
                    product_data['url'] = self._get_full_url(link.get('href'))
                    break
            
            # If no link found, try text content
            if not product_data.get('name'):
                text_content = element.get_text(strip=True)
                if text_content and len(text_content) > 10:
                    product_data['name'] = text_content[:100]
                    product_data['url'] = 'N/A'
            
            # Extract price
            price_selectors = [
                '.price', '.prd-price', '.lst-price', '.product-price',
                '[class*="price"]', '[class*="cost"]', '[class*="rate"]',
                '.getquote', 'p.getquote', 'p.price', 'p.getquote',
            ]
            
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text:
                        product_data['price'] = price_text
                        break
            
            # Fallback for 'Ask Price'
            if 'price' not in product_data:
                ask_price_elem = element.find(string=lambda t: t and 'Ask Price' in t)
                if ask_price_elem:
                    product_data['price'] = ask_price_elem.strip()
            
            # Extract company
            company_selectors = [
                '.companyname a', '.company-name', '.prd-comp-name', '.lst-comp-name',
                '.seller-name', '[class*="company"]', '[class*="seller"]', '[class*="supplier"]'
            ]
            
            for selector in company_selectors:
                company_elem = element.select_one(selector)
                if company_elem:
                    company_text = company_elem.get_text(strip=True)
                    if company_text:
                        product_data['company'] = company_text
                        break
            
            # Extract location
            location_selectors = [
                '.newLocationUi span.elps', '.location', '.prd-comp-loc', '.lst-comp-loc',
                '[class*="location"]', '[class*="city"]', '[class*="address"]'
            ]
            
            for selector in location_selectors:
                location_elem = element.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if location_text:
                        product_data['location'] = location_text
                        break
            
            # Set defaults
            product_data.setdefault('price', 'N/A')
            product_data.setdefault('company', 'N/A')
            product_data.setdefault('location', 'N/A')
            product_data.setdefault('url', 'N/A')
            
            return product_data if product_data.get('name') else None
            
        except Exception as e:
            print(f"Error parsing element: {e}")
            return None
    
    def _extract_from_all_links(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """
        Extract products from all relevant links when normal extraction fails
        """
        products = []
        
        # Find all links that might be products
        all_links = soup.find_all('a', href=True)
        product_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Filter for product-related links
            if any(keyword in href.lower() for keyword in ['proddetail', 'product', 'item']) and text:
                product_links.append(link)
        
        print(f"Found {len(product_links)} potential product links")
        
        for i, link in enumerate(product_links[:max_results]):
            try:
                product_data = {
                    'name': link.get('title') or link.get_text(strip=True),
                    'url': self._get_full_url(link.get('href')),
                    'company': 'N/A',
                    'location': 'N/A',
                    'price': 'N/A'
                }
                
                if product_data['name'] and len(product_data['name']) > 5:
                    products.append(product_data)
                    print(f"Extracted from link: {product_data['name'][:50]}...")
                    
            except Exception as e:
                print(f"Error extracting from link {i+1}: {e}")
                continue
        
        return products
    
    def _alternative_search_approach(self, part_name: str, max_results: int) -> List[Dict]:
        """
        Alternative search approach using Google
        """
        try:
            print("Trying Google search for IndiaMART results...")
            
            # Use Google to find IndiaMART pages
            google_query = f"site:indiamart.com {part_name}"
            google_url = f"https://www.google.com/search?q={quote_plus(google_query)}"
            
            response = self.session.get(google_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract IndiaMART URLs
                indiamart_urls = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and 'indiamart.com' in href:
                        if href.startswith('/url?q='):
                            actual_url = href.split('/url?q=')[1].split('&')[0]
                            if 'indiamart.com' in actual_url:
                                indiamart_urls.append(actual_url)
                
                print(f"Found {len(indiamart_urls)} IndiaMART URLs from Google")
                
                # Extract product info from these URLs
                products = []
                for url in indiamart_urls[:max_results]:
                    try:
                        product_info = self._extract_product_from_url(url)
                        if product_info:
                            products.append(product_info)
                        time.sleep(random.uniform(1, 2))
                    except Exception as e:
                        print(f"Error extracting from {url}: {e}")
                        continue
                
                return products
            
            return []
            
        except Exception as e:
            print(f"Alternative search failed: {e}")
            return []
    
    def _extract_product_from_url(self, url: str) -> Optional[Dict]:
        """
        Extract product information from a specific URL
        """
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                product_data = {
                    'url': url,
                    'name': 'N/A',
                    'company': 'N/A',
                    'location': 'N/A',
                    'price': 'N/A'
                }
                
                # Extract name from title or h1
                title_elem = soup.find('title')
                if title_elem:
                    product_data['name'] = title_elem.get_text(strip=True)
                else:
                    h1_elem = soup.find('h1')
                    if h1_elem:
                        product_data['name'] = h1_elem.get_text(strip=True)
                
                return product_data if product_data['name'] != 'N/A' else None
            
            return None
            
        except Exception as e:
            print(f"Error extracting from URL: {e}")
            return None
    
    def _get_full_url(self, url: str) -> str:
        """Convert relative URL to absolute URL"""
        if not url:
            return "N/A"
        
        if url.startswith('http'):
            return url
        elif url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.base_url}{url}"
        else:
            return f"{self.base_url}/{url}"
    
    def save_to_csv(self, products: List[Dict], filename: str = "indiamart_parts.csv"):
        """Save extracted data to CSV file"""
        if not products:
            print("No products to save")
            return
        
        df = pd.DataFrame(products)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    
    def save_to_json(self, products: List[Dict], filename: str = "indiamart_parts.json"):
        """Save extracted data to JSON file"""
        if not products:
            print("No products to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

# Usage example
def main():
    # Try with Selenium first, fallback to requests
    scraper = IndiaMartScraper(use_selenium=True)
    
    try:
        # Get part name from user
        part_name = input("Enter the part name to search: ").strip()
        
        if not part_name:
            print("Please enter a valid part name")
            return
        
        # Search for parts
        print(f"\nSearching for parts: {part_name}")
        products = scraper.search_parts(part_name, max_results=10)
        
        if not products:
            print("No products found. Check debug files for more information.")
            return
        
        print(f"\nFound {len(products)} products:")
        
        # Display results
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.get('name', 'Unknown Product')}")
            print(f"   Company: {product.get('company', 'N/A')}")
            print(f"   Location: {product.get('location', 'N/A')}")
            print(f"   Price: {product.get('price', 'N/A')}")
            if product.get('url') != 'N/A':
                print(f"   URL: {product.get('url', 'N/A')}")
        
        # Save results
        scraper.save_to_csv(products)
        scraper.save_to_json(products)
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main()