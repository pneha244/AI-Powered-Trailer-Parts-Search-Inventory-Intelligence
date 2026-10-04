import streamlit as st
import pandas as pd
from rag_search import RAGSearch
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="Trailer Parts Intelligent Search", layout="wide")

# Navigation
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("🚛 Trailer Parts Intelligent Search")
    st.markdown("Enter a trailer part name to get the best recommendation and 5 alternatives from the database.")
with col2:
    if st.button("📦 Inventory", help="View all items in the database"):
        st.switch_page("pages/Inventory.py")
with col3:
    if st.button("🏠 Home", help="Go to home page"):
        st.switch_page("Home.py")

USD_TO_INR = 86.0  # You can update this rate as needed
def convert_usd_to_inr(price_str):
    if not price_str or 'USD' not in price_str:
        return price_str
    try:
        value = ''.join(c for c in price_str if c.isdigit() or c == '.' or c == '-')
        inr_value = float(value) * USD_TO_INR
        return f"₹{inr_value:,.2f}"
    except:
        return price_str

# Helper to strip HTML tags and markdown using BeautifulSoup
BOLD_MD_RE = re.compile(r'\*\*([^*]+)\*\*')
ITALIC_MD_RE = re.compile(r'\*([^*]+)\*')
def strip_html(text):
    if not text:
        return text
    text = BeautifulSoup(text, "html.parser").get_text()
    text = BOLD_MD_RE.sub(r'\1', text)
    text = ITALIC_MD_RE.sub(r'\1', text)
    return text.strip()

def clean_url(url):
    if not url:
        return "#"
    url = strip_html(url)
    url = url.strip().lstrip('*').strip()
    url = re.sub(r'\*+', '', url)
    url = url.replace(' ', '')
    return url

# Initialize session state for alternatives and sort order
if 'alt_products' not in st.session_state:
    st.session_state['alt_products'] = []
if 'sort_order' not in st.session_state:
    st.session_state['sort_order'] = 'Ascending'
if 'search_done' not in st.session_state:
    st.session_state['search_done'] = False

with st.form("search_form"):
    query = st.text_input("Enter trailer part name to search:", "")
    submitted = st.form_submit_button("Search")

if submitted:
    if not query.strip():
        st.error("Please enter a valid search term.")
        st.session_state['search_done'] = False
    else:
        with st.spinner("Searching the vector database, please wait..."):
            rag = RAGSearch(top_k=6)
            results = rag.retrieve(query)
            metadatas = results["metadatas"][0] if results and results.get("metadatas") and results["metadatas"][0] else []
        if not metadatas:
            st.warning("Product not present in database.")
            st.session_state['alt_products'] = []
            st.session_state['search_done'] = False
        else:
            context = rag.format_context(results)
            best_product_response = rag.ask_llm(query, context)
            # Extract best product details
            name_match = re.search(r'Product Name:\s*(.*)', best_product_response)
            price_match = re.search(r'Price:\s*(.*)', best_product_response)
            source_match = re.search(r'Source:\s*(.*)', best_product_response)
            url_match = re.search(r'URL:\s*(.*)', best_product_response)
            rating_match = re.search(r'Rating:\s*(.*)', best_product_response)
            seller_match = re.search(r'Seller:\s*(.*)', best_product_response)
            seller_rating_match = re.search(r'Seller Rating:\s*(.*)', best_product_response)
            best_name = strip_html(name_match.group(1).strip()) if name_match else "Best Product"
            best_price = strip_html(price_match.group(1).strip()) if price_match else "N/A"
            best_source = strip_html(source_match.group(1).strip()) if source_match else "N/A"
            best_url = clean_url(url_match.group(1)) if url_match else "#"
            # Convert USD to INR if needed
            best_price_display = convert_usd_to_inr(best_price)
            # Store alternatives in session state
            alt_products = metadatas[:5] if len(metadatas) > 1 else []
            for p in alt_products:
                for k in ['name', 'price', 'source', 'url', 'rating', 'seller', 'seller_rating']:
                    if k in p and isinstance(p[k], str):
                        p[k] = strip_html(p[k])
                if 'url' in p and isinstance(p['url'], str):
                    p['url'] = clean_url(p['url'])
                # Convert USD to INR for alternatives
                if 'price' in p:
                    p['price'] = convert_usd_to_inr(p['price'])
            st.session_state['alt_products'] = alt_products
            st.session_state['best_product'] = {
                'name': best_name,
                'price': best_price_display,
                'source': best_source,
                'url': best_url,
                'rating': strip_html(rating_match.group(1).strip()) if rating_match else None,
                'seller': strip_html(seller_match.group(1).strip()) if seller_match else None,
                'seller_rating': strip_html(seller_rating_match.group(1).strip()) if seller_rating_match else None
            }
            st.session_state['search_done'] = True
            st.session_state['sort_order'] = 'Ascending'

# Show results if a search was done and there are alternatives or a best product
if st.session_state.get('search_done', False):
    best = st.session_state.get('best_product', {})
    # Build HTML for recommended product card (simple version)
    best_link_html = f'<p style="margin: 0.2rem 0; color: #7ec4cf;"><b>Product Link:</b> <a href="{best.get("url", "#")}" target="_blank" style="color: #7ec4cf; text-decoration: underline;">Product Link</a></p>' if best.get("url", "#") and best.get("url", "#") != "#" else ''
    # Show rating for Amazon, seller for eBay
    rating_or_seller_html = ''
    if 'amazon' in best.get('source', '').lower() and best.get('rating'):
        val = best.get('rating')
        try:
            valf = float(val)
            stars = '⭐' * int(round(valf))
            val = f"{stars} ({valf}/5)"
        except:
            pass
        rating_or_seller_html = f'<p style="margin: 0.2rem 0; color: #e0e0e0;"><b>Rating:</b> {val}</p>'
    elif 'ebay' in best.get('source', '').lower() and best.get('seller'):
        seller_info = best.get('seller')
        if best.get('seller_rating'):
            seller_info += f" ({best.get('seller_rating')})"
        rating_or_seller_html = f'<p style="margin: 0.2rem 0; color: #e0e0e0;"><b>Seller:</b> {seller_info}</p>'
    best_product_html = f"""
        <div style='background: #23272f; border-radius: 16px; padding: 2rem 2rem 1.5rem 2rem; margin-bottom: 2rem; position: relative; box-shadow: 0 4px 16px rgba(0,0,0,0.10); border: 1px solid #444;'>
            <div style='position: absolute; top: 1.2rem; right: 2rem;'>
                <span style='background: #3d4859; color: #f7c873; padding: 0.4em 1em; border-radius: 12px; font-weight: bold; font-size: 1.1em;'>Recommended</span>
            </div>
            <h3 style='margin-bottom: 0.5rem; color: #f7c873;'>{best.get('name', 'Best Product')}</h3>
            <p style='margin: 0.2rem 0; color: #e0e0e0;'><b>Price:</b> {best.get('price', 'N/A')} &nbsp; <b>Source:</b> {best.get('source', 'N/A')}</p>
            {best_link_html}
            {rating_or_seller_html}
        </div>
    """
    st.markdown(best_product_html, unsafe_allow_html=True)

    alt_products = st.session_state.get('alt_products', [])
    if alt_products:
        st.subheader("🔎 5 Other Relevant Products")
        sort_order = st.radio("Sort alternatives by price:", ["Ascending", "Descending"], horizontal=True, key="sort_order_radio", index=0 if st.session_state['sort_order'] == 'Ascending' else 1)
        st.session_state['sort_order'] = sort_order
        def parse_price(p):
            price = p.get('price', '')
            price = ''.join(c for c in price if c.isdigit() or c == '.' or c == '-')
            try:
                return float(price)
            except:
                return float('inf')
        alt_products_sorted = sorted(
            alt_products,
            key=parse_price,
            reverse=(sort_order == "Descending")
        )
        for p in alt_products_sorted:
            link_html = f'<p style="margin: 0.2rem 0; color: #7ec4cf;"><b>Product Link:</b> <a href="{p.get("url", "#")}" target="_blank" style="color: #7ec4cf; text-decoration: underline;">Product Link</a></p>' if p.get("url", "#") and p.get("url", "#") != "#" else ''
            rating_or_seller_html = ''
            if 'amazon' in p.get('source', '').lower() and p.get('rating'):
                val = p.get('rating')
                try:
                    valf = float(val)
                    stars = '⭐' * int(round(valf))
                    val = f"{stars} ({valf}/5)"
                except:
                    pass
                rating_or_seller_html = f'<p style="margin: 0.2rem 0;"><b>Rating:</b> {val}</p>'
            elif 'ebay' in p.get('source', '').lower() and p.get('seller'):
                seller_info = p.get('seller')
                if p.get('seller_rating'):
                    seller_info += f" ({p.get('seller_rating')})"
                rating_or_seller_html = f'<p style="margin: 0.2rem 0;"><b>Seller:</b> {seller_info}</p>'
            alt_product_html = f"""
                <div style='background: #23272f; border-radius: 14px; padding: 1.2rem 1.5rem 1rem 1.5rem; margin-bottom: 1.5rem; color: #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.10); border: 1px solid #444;'>
                    <h4 style='margin-bottom: 0.3rem; color: #f7c873;'>{p.get('name', p.get('title', 'No Title'))}</h4>
                    <p style='margin: 0.2rem 0;'><b>Price:</b> {p.get('price', 'N/A')} &nbsp; <b>Source:</b> {p.get('source', 'N/A')}</p>
                    {link_html}
                    {rating_or_seller_html}
                </div>
            """
            st.markdown(alt_product_html, unsafe_allow_html=True)
