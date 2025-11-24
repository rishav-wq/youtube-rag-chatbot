# 🎥 YouTube RAG Chatbot Pro

An advanced Retrieval-Augmented Generation (RAG) chatbot that enables intelligent conversations about YouTube videos with multi-language support and web-enriched context.

## 🚀 Live Demo

**Try it now:** [https://youtube-rag-chatbot-umk42rgntkhgfdw3hujf4f.streamlit.app/](https://youtube-rag-chatbot-umk42rgntkhgfdw3hujf4f.streamlit.app/)

## ✨ Features

### Core Capabilities
- 🎬 **YouTube Transcript Extraction** - Automatically fetches video transcripts with multi-language fallback
- 🤖 **RAG-Powered Q&A** - Ask questions and get accurate answers based on video content
- 🌐 **Web Enrichment** - Optionally enhances responses with relevant web context
- 📊 **Source Tracking** - See exactly where each answer comes from
- 💬 **Chat History** - Maintains conversation context for follow-up questions

### Enrichment Modes
Choose from multiple enrichment strategies to balance speed vs. depth:

- **Transcript Only** - Fastest, relies solely on video content
- **Minimal** - Adds basic background context
- **Balanced** ⭐ (Recommended) - Best mix of accuracy and context
- **Comprehensive** - Includes all available sources
- **Academic** - Focuses on research and scholarly content

### Technical Highlights
- 🚀 **Fast & Free** - Powered by Groq's LLaMA 3.3 70B model
- 🔍 **FAISS Vector Store** - Efficient semantic search
- 🌍 **Multi-Language Support** - Automatically handles non-English transcripts
- 📈 **Smart Chunking** - Optimized text splitting for better retrieval
- 🎯 **Configurable** - Flexible enrichment strategies

## 🛠️ Technology Stack

- **Frontend:** Streamlit
- **LLM:** Groq (LLaMA 3.3 70B Versatile)
- **Embeddings:** HuggingFace (all-MiniLM-L6-v2)
- **Vector Store:** FAISS
- **Framework:** LangChain
- **APIs:** 
  - YouTube Transcript API
  - Serper API (for web enrichment)

## 📋 Prerequisites

- Python 3.8+
- Groq API Key (free at [console.groq.com](https://console.groq.com))
- Serper API Key (optional, for web enrichment at [serper.dev](https://serper.dev))

## 🔧 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/rishav-wq/youtube-rag-chatbot.git
cd youtube-rag-chatbot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**

Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
SERPER_API_KEY=your_serper_api_key_here  # Optional
```

4. **Run the application:**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage

1. **Paste a YouTube URL** in the sidebar
2. **Select enrichment mode** based on your needs:
   - Use "Transcript Only" for fastest, most accurate responses about the video
   - Use "Balanced" for enhanced context with web information
3. **Click "Create RAG System"** to process the video
4. **Ask questions** in the chat interface
5. **View sources** to see where information came from

### Example Questions
- "What are the main points discussed in this video?"
- "Can you summarize the key takeaways?"
- "What does the speaker say about [specific topic]?"
- "How does this compare to [related topic]?"

## 📁 Project Structure

```
youtube-rag-chatbot-pro/
│
├── .env                    # Environment variables (not in repo)
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── app.py                # Main Streamlit application
│
└── src/
    ├── __init__.py
    └── rag_pipeline.py   # Core RAG logic and enrichment
```

## 🔑 Key Components

### RAG Pipeline (`src/rag_pipeline.py`)
- **Transcript Extraction:** Multi-language support with automatic fallback
- **Content Enrichment:** Configurable web search strategies
- **Vector Store:** FAISS-based semantic search
- **Source Tracking:** Complete attribution for all information

### Streamlit App (`app.py`)
- **User Interface:** Clean, intuitive chat interface
- **Configuration:** Easy-to-use enrichment settings
- **Visualization:** Metrics and source display
- **Session Management:** Persistent chat history

## 🌟 Advanced Features

### Multi-Language Support
Automatically detects and handles videos in any language with available transcripts:
```python
# Tries English first, then falls back to available languages
transcript = fetch_transcript(video_id)
```

### Configurable Enrichment
```python
config = EnrichmentConfig(
    enabled=True,
    strategies=['background', 'discussions'],
    max_results_per_strategy=1000
)
```

### Source Attribution
Every response includes sources with:
- Original content excerpts
- Relevance scores
- Source types (transcript/web)
- URLs for web sources

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for the RAG framework
- [Groq](https://groq.com/) for fast, free LLM inference
- [Streamlit](https://streamlit.io/) for the amazing web framework
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api) for transcript extraction

## 📧 Contact

**Rishav** - [@rishav-wq](https://github.com/rishav-wq)

**Project Link:** [https://github.com/rishav-wq/youtube-rag-chatbot](https://github.com/rishav-wq/youtube-rag-chatbot)

**Live Demo:** [https://youtube-rag-chatbot-umk42rgntkhgfdw3hujf4f.streamlit.app/](https://youtube-rag-chatbot-umk42rgntkhgfdw3hujf4f.streamlit.app/)

---

⭐ **Star this repo** if you find it helpful!
