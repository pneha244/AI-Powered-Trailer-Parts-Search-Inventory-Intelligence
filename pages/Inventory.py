import streamlit as st
import chromadb
import pandas as pd
from datetime import datetime
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="Inventory & Configuration", layout="wide")

# Navigation
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("📦 Inventory & Configuration")
    st.markdown("View all items stored in the trailer parts database.")
with col2:
    if st.button("🔍 Search", help="Go back to search page"):
        st.switch_page("pages/Search.py")
with col3:
    if st.button("🏠 Home", help="Go to home page"):
        st.switch_page("Home.py")

# Helper functions from the main app
USD_TO_INR = 86.0

def convert_usd_to_inr(price_str):
    if not price_str or 'USD' not in price_str:
        return price_str
    try:
        value = ''.join(c for c in price_str if c.isdigit() or c == '.' or c == '-')
        inr_value = float(value) * USD_TO_INR
        return f"₹{inr_value:,.2f}"
    except:
        return price_str

def strip_html(text):
    if not text:
        return text
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    return text.strip()

def clean_url(url):
    if not url:
        return "#"
    url = strip_html(url)
    url = url.strip().lstrip('*').strip()
    url = re.sub(r'\*+', '', url)
    url = url.replace(' ', '')
    return url

# Initialize database connection
@st.cache_resource
def get_database_info():
    try:
        client = chromadb.PersistentClient(path="parts_db")
        collection = client.get_collection(name="trailer_parts")
        return collection, client
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None, None

# Get database info
collection, client = get_database_info()

if collection is None:
    st.error("❌ Could not connect to the database. Please ensure the database exists and is accessible.")
    st.stop()

# Get all items from database
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_items():
    try:
        # Get all items from the collection
        results = collection.get(
            include=["metadatas", "documents", "embeddings"]
        )
        return results
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return None

# Sidebar for filters
st.sidebar.header("🔍 Filters")

# Get all items
all_items = get_all_items()

if all_items is None:
    st.error("❌ Could not retrieve data from database.")
    st.stop()

# Extract metadata
metadatas = all_items.get("metadatas", [])
documents = all_items.get("documents", [])
ids = all_items.get("ids", [])

# Create filters
sources = list(set([meta.get('source', 'Unknown') for meta in metadatas if meta]))
source_filter = st.sidebar.multiselect(
    "Filter by Source:",
    options=sources,
    default=sources
)

# Price range filter
prices = []
for meta in metadatas:
    if meta and 'price' in meta:
        price_str = str(meta['price'])
        try:
            # Extract numeric value
            price_val = re.findall(r'[\d,]+\.?\d*', price_str)
            if price_val:
                price_num = float(price_val[0].replace(',', ''))
                prices.append(price_num)
        except:
            pass

if prices:
    min_price = min(prices)
    max_price = max(prices)
    price_range = st.sidebar.slider(
        "Price Range:",
        min_value=float(min_price),
        max_value=float(max_price),
        value=(float(min_price), float(max_price)),
        step=1.0
    )
else:
    price_range = (0, 1000)

# Search filter
search_term = st.sidebar.text_input("Search by name:", "")

# Filter items based on criteria
filtered_items = []
for i, meta in enumerate(metadatas):
    if not meta:
        continue
    
    # Source filter
    if meta.get('source') not in source_filter:
        continue
    
    # Search filter
    if search_term and search_term.lower() not in meta.get('name', '').lower():
        continue
    
    # Price filter
    if 'price' in meta:
        price_str = str(meta['price'])
        try:
            price_val = re.findall(r'[\d,]+\.?\d*', price_str)
            if price_val:
                price_num = float(price_val[0].replace(',', ''))
                if not (price_range[0] <= price_num <= price_range[1]):
                    continue
        except:
            pass
    
    filtered_items.append({
        'id': ids[i] if i < len(ids) else f"item_{i}",
        'metadata': meta,
        'document': documents[i] if i < len(documents) else ""
    })

# Display statistics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Items", len(metadatas))
with col2:
    st.metric("Filtered Items", len(filtered_items))
with col3:
    amazon_count = len([m for m in metadatas if m and m.get('source') == 'amazon.in'])
    st.metric("Amazon Items", amazon_count)
with col4:
    ebay_count = len([m for m in metadatas if m and m.get('source') == 'ebay.com'])
    st.metric("eBay Items", ebay_count)

# Sort options
sort_by = st.selectbox(
    "Sort by:",
    ["Name", "Price", "Source", "Rating"],
    index=0
)

# Sort filtered items
if sort_by == "Name":
    filtered_items.sort(key=lambda x: x['metadata'].get('name', '').lower())
elif sort_by == "Price":
    def get_price(item):
        price_str = str(item['metadata'].get('price', '0'))
        try:
            price_val = re.findall(r'[\d,]+\.?\d*', price_str)
            return float(price_val[0].replace(',', '')) if price_val else 0
        except:
            return 0
    filtered_items.sort(key=get_price)
elif sort_by == "Source":
    filtered_items.sort(key=lambda x: x['metadata'].get('source', ''))
elif sort_by == "Rating":
    def get_rating(item):
        rating = item['metadata'].get('rating', '0')
        try:
            return float(rating) if rating else 0
        except:
            return 0
    filtered_items.sort(key=get_rating, reverse=True)

# Display items
st.subheader(f"📋 Inventory Items ({len(filtered_items)} items)")

# Pagination
items_per_page = 20
total_pages = (len(filtered_items) + items_per_page - 1) // items_per_page
current_page = st.selectbox("Page:", range(1, total_pages + 1), index=0)

start_idx = (current_page - 1) * items_per_page
end_idx = start_idx + items_per_page
current_items = filtered_items[start_idx:end_idx]

# Display items in a grid
for i, item in enumerate(current_items):
    meta = item['metadata']
    
    # Clean and format data
    name = strip_html(meta.get('name', 'No Name'))
    price = convert_usd_to_inr(meta.get('price', 'N/A'))
    source = meta.get('source', 'Unknown')
    url = clean_url(meta.get('url', ''))
    rating = meta.get('rating', 'N/A')
    seller = meta.get('seller', 'N/A')
    seller_rating = meta.get('seller_rating', 'N/A')
    
    # Create card
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{name}**")
            st.markdown(f"💰 **Price:** {price} | 🏪 **Source:** {source}")
            if url and url != "#":
                st.markdown(f"🔗 [View Product]({url})")
            
            # Show rating or seller info
            if 'amazon' in source.lower() and rating and rating != 'N/A':
                try:
                    rating_val = float(rating)
                    stars = '⭐' * int(round(rating_val))
                    st.markdown(f"⭐ **Rating:** {stars} ({rating_val}/5)")
                except:
                    pass
            elif 'ebay' in source.lower() and seller and seller != 'N/A':
                seller_info = seller
                if seller_rating and seller_rating != 'N/A':
                    seller_info += f" ({seller_rating})"
                st.markdown(f"👤 **Seller:** {seller_info}")
        
        with col2:
            # Item ID for reference
            st.markdown(f"**ID:** {item['id'][:20]}...")
            
            # Additional metadata
            if meta.get('asin'):
                st.markdown(f"**ASIN:** {meta['asin']}")
            if meta.get('item_id'):
                st.markdown(f"**Item ID:** {meta['item_id']}")
        
        st.divider()

# Export functionality
st.sidebar.divider()
st.sidebar.subheader("📊 Export Data")

if st.sidebar.button("Export to CSV"):
    # Prepare data for export
    export_data = []
    for item in filtered_items:
        meta = item['metadata']
        export_data.append({
            'ID': item['id'],
            'Name': strip_html(meta.get('name', 'No Name')),
            'Price': convert_usd_to_inr(meta.get('price', 'N/A')),
            'Source': meta.get('source', 'Unknown'),
            'URL': clean_url(meta.get('url', '')),
            'Rating': meta.get('rating', 'N/A'),
            'Seller': meta.get('seller', 'N/A'),
            'Seller Rating': meta.get('seller_rating', 'N/A'),
            'ASIN': meta.get('asin', ''),
            'Item ID': meta.get('item_id', ''),
            'Availability': meta.get('availability', 'N/A'),
            'Prime': meta.get('prime', 'N/A'),
            'Review Count': meta.get('review_count', 'N/A')
        })
    
    df = pd.DataFrame(export_data)
    csv = df.to_csv(index=False)
    
    st.sidebar.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"trailer_parts_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# Database info
st.sidebar.divider()
st.sidebar.subheader("🗄️ Database Info")
st.sidebar.markdown(f"**Collection:** trailer_parts")
st.sidebar.markdown(f"**Total Items:** {len(metadatas)}")
st.sidebar.markdown(f"**Sources:** {', '.join(sources)}")

# Clear cache button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun() 