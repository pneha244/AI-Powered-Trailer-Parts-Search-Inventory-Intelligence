import streamlit as st

st.set_page_config(page_title="Trailer Parts Finder", layout="wide")

st.title("🚛 Smart Part Finder")
st.markdown("Welcome to the intelligent trailer parts search and inventory management system.")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔍 Search Parts")
    st.markdown("""
    - **Intelligent Search**: Find the best trailer parts using AI-powered recommendations
    - **Multiple Sources**: Search across Amazon and eBay simultaneously
    - **Smart Recommendations**: Get the best product with 5 alternatives
    - **Price Conversion**: Automatic USD to INR conversion
    """)
    
    if st.button("🔍 Start Searching", type="primary"):
        st.switch_page("pages/Search.py")

with col2:
    st.subheader("📦 Inventory Management")
    st.markdown("""
    - **View All Items**: Browse the complete database inventory
    - **Advanced Filtering**: Filter by source, price, and search terms
    - **Export Data**: Download inventory as CSV
    - **Real-time Stats**: View database statistics and metrics
    """)
    
    if st.button("📦 View Inventory"):
        st.switch_page("pages/Inventory.py")

st.markdown("---")

st.subheader("📊 System Features")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🤖 AI-Powered Search
    - Vector database with semantic search
    - RAG (Retrieval-Augmented Generation) for intelligent recommendations
    - Multi-source data integration
    """)

with col2:
    st.markdown("""
    ### 🗄️ Database Management
    - ChromaDB vector database
    - Persistent storage with metadata
    - Real-time data updates
    """)

with col3:
    st.markdown("""
    ### 📈 Analytics & Export
    - Comprehensive filtering options
    - Data export capabilities
    - Performance metrics
    """)

st.markdown("---")

st.subheader("🚀 Quick Start")
st.markdown("""
1. **Search Parts**: Click 'Start Searching' to find trailer parts with AI recommendations
2. **View Inventory**: Click 'View Inventory' to browse all items in the database
3. **Export Data**: Use the inventory page to export filtered data as CSV
""")

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit, ChromaDB, and AI-powered search capabilities*") 