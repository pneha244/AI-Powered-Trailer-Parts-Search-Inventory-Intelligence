# 🚛 Trailer Parts Intelligent Search System

A comprehensive AI-powered trailer parts search and inventory management system built with Streamlit, ChromaDB, and Google's Gemini AI. This system provides intelligent product recommendations, multi-source data integration, and comprehensive inventory management capabilities.

## 🎯 Features

### 🔍 Intelligent Search
- **AI-Powered Recommendations**: Uses RAG (Retrieval-Augmented Generation) with Google Gemini AI
- **Multi-Source Integration**: Searches across Amazon and eBay simultaneously
- **Semantic Search**: Vector database with advanced similarity matching
- **Smart Filtering**: Price conversion (USD to INR), rating analysis, and seller information

### 📦 Inventory Management
- **Complete Database View**: Browse all items stored in the vector database
- **Advanced Filtering**: Filter by source, price range, and search terms
- **Real-time Statistics**: View database metrics and performance indicators
- **Export Capabilities**: Download filtered data as CSV files

### 🗄️ Database Features
- **ChromaDB Vector Database**: Persistent storage with metadata
- **Embedding Models**: Sentence transformers for semantic search
- **Real-time Updates**: Dynamic data loading and caching

## 📋 System Requirements

### Software Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows 10/11, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free space for database and models

### Hardware Requirements
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: SSD recommended for better performance

## 🚀 Quick Start (5-Minute Setup)

### Method 1: Automated Setup (Recommended)
```bash
# 1. Download and extract the project
# 2. Navigate to the scripts folder
cd smart_part_finder/scripts

# 3. Run the automated setup
python setup.py

# 4. Start the application (if not started automatically)
streamlit run Home.py
```

### Method 2: Manual Installation
```bash
# 1. Navigate to the project root
cd smart_part_finder

# 2. Install dependencies
pip install -r requirements.txt

# 3. Navigate to scripts folder
cd scripts

# 4. Run the application
streamlit run Home.py
```

### Accessing the Application
1. The application will automatically open in your default web browser
2. If it doesn't open automatically, navigate to: `http://localhost:8501`
3. The application runs on port 8501 by default

## 📖 Usage Guide

### Accessing the Application
1. The application will automatically open in your default web browser
2. If it doesn't open automatically, navigate to: `http://localhost:8501`
3. The application runs on port 8501 by default

## 📁 Project Structure

```
smart_part_finder/
├── 📄 README.md                  # This file - comprehensive documentation
├── 📄 requirements.txt           # Python dependencies with versions
├── 📁 scripts/                   # Main application folder
│   ├── 📄 Home.py               # Main application entry point
│   ├── 📄 setup.py              # Automated installation script
│   ├── 📁 pages/                # Streamlit multi-page app
│   │   ├── 📄 Search.py         # Intelligent search interface
│   │   └── 📄 Inventory.py      # Database inventory viewer
│   ├── 📄 rag_search.py         # RAG implementation with Gemini AI
│   ├── 📄 intelligent_search.py # Vector search functionality
│   ├── 📄 scrape_parts.py       # Web scraping for Amazon/eBay
│   └── 📁 parts_db/             # ChromaDB vector database
```

## 📖 Usage Guide

### 🏠 Home Page
- **Overview**: Welcome page with system features and quick start guide
- **Navigation**: Easy access to Search and Inventory pages
- **System Information**: Overview of AI capabilities and database features

### 🔍 Search Page
1. **Enter Search Query**: Type the trailer part name you're looking for
2. **Click Search**: The system will search the database and provide recommendations
3. **View Results**: 
   - **Recommended Product**: AI-selected best match with detailed information
   - **5 Alternatives**: Additional options with pricing and source information
   - **Price Conversion**: Automatic USD to INR conversion
   - **Rating Information**: Amazon ratings or eBay seller information

### 📦 Inventory Page
1. **Browse All Items**: View complete database inventory
2. **Apply Filters**:
   - **Source Filter**: Filter by Amazon or eBay
   - **Price Range**: Set minimum and maximum price
   - **Search Terms**: Find specific items by name
3. **Sort Options**: Sort by name, price, source, or rating
4. **Export Data**: Download filtered results as CSV
5. **Statistics**: View real-time database metrics

## 🔧 Configuration

### API Keys
The application uses Google's Gemini AI for intelligent recommendations. The API key is configured in the code for demonstration purposes. For production use:

1. **Get Google AI API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Update Configuration**: Replace the API key in `pages/Search.py` and `rag_search.py`

### Database Configuration
- **Location**: Database files are stored in the `parts_db/` directory
- **Collection**: Default collection name is "trailer_parts"
- **Persistence**: Data is automatically saved and persists between sessions

### Price Conversion
- **Default Rate**: USD to INR conversion rate is set to 86.0
- **Customization**: Update the `USD_TO_INR` variable in the code files

## 📊 Database Structure

### Data Sources
- **Amazon.in**: Product listings with ratings, reviews, and Prime status
- **eBay.com**: Product listings with seller information and ratings

### Metadata Fields
- **name**: Product name/title
- **price**: Product price (with currency)
- **source**: Data source (amazon.in or ebay.com)
- **url**: Direct product link
- **rating**: Product rating (Amazon)
- **seller**: Seller name (eBay)
- **seller_rating**: Seller rating (eBay)
- **asin**: Amazon Standard Identification Number
- **item_id**: eBay item identifier
- **availability**: Stock status
- **prime**: Amazon Prime eligibility
- **review_count**: Number of reviews

## 🛠️ Troubleshooting

### Quick Fixes
```bash
# If setup fails
pip install -r requirements.txt
cd scripts
streamlit run Home.py

# If app doesn't start
streamlit run Home.py --server.port 8502

# If database is empty
# Run scraping scripts to populate data first
```

### Common Issues
- **Installation Errors**: Use `pip install --trusted-host pypi.org -r requirements.txt`
- **Port Conflicts**: Try different port with `--server.port 8502`
- **Memory Issues**: Close other apps, restart application
- **Database Issues**: Ensure `parts_db/` directory exists

## 🔒 Security Considerations

### API Keys
- **Development**: API keys are included for demonstration
- **Production**: Use environment variables for API keys
- **Rotation**: Regularly rotate API keys

### Data Privacy
- **Local Storage**: All data is stored locally
- **No External Sharing**: No data is transmitted to external servers
- **User Control**: Users have full control over their data

## 📈 Performance Metrics

### Search Performance
- **Response Time**: Typically 2-5 seconds for search queries
- **Accuracy**: High relevance scores for semantic search
- **Scalability**: Handles thousands of products efficiently

### Database Performance
- **Storage**: Efficient vector storage with ChromaDB
- **Query Speed**: Fast similarity search with embeddings
- **Memory Usage**: Optimized for typical desktop systems

## 🤝 Support and Maintenance

### Regular Maintenance
- **Update Dependencies**: Regularly update Python packages
- **Database Backup**: Backup the `parts_db/` directory
- **API Key Rotation**: Rotate API keys periodically

### Monitoring
- **Application Logs**: Check Streamlit logs for errors
- **Database Health**: Monitor database size and performance
- **API Usage**: Monitor Google AI API usage

## 📝 License and Attribution

### Open Source Components
- **Streamlit**: Web application framework
- **ChromaDB**: Vector database
- **Sentence Transformers**: Embedding models
- **Google Generative AI**: LLM integration

### Custom Development
- **Search Algorithms**: Custom RAG implementation
- **UI/UX Design**: Custom Streamlit interface
- **Data Processing**: Custom scraping and processing logic

