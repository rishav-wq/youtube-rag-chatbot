import re
import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_community.vectorstores import FAISS
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.embeddings import FakeEmbeddings
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from urllib.parse import urlparse, parse_qs
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# ==================== CONFIGURATION SYSTEM ====================

@dataclass
class EnrichmentConfig:
    """Configuration for content enrichment"""
    enabled: bool = True
    strategies: List[str] = None  # ['background', 'discussions', 'academic', 'current']
    max_results_per_strategy: int = 1000
    track_sources: bool = True
    
    def __post_init__(self):
        if self.strategies is None:
            self.strategies = ['background', 'discussions']
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config_dict: dict):
        return cls(**config_dict)
    
    @classmethod
    def preset_minimal(cls):
        """Minimal enrichment - fastest"""
        return cls(enabled=True, strategies=['background'])
    
    @classmethod
    def preset_balanced(cls):
        """Balanced enrichment - recommended"""
        return cls(enabled=True, strategies=['background', 'discussions'])
    
    @classmethod
    def preset_comprehensive(cls):
        """Comprehensive enrichment - most thorough"""
        return cls(enabled=True, strategies=['background', 'discussions', 'academic', 'current'])
    
    @classmethod
    def preset_academic(cls):
        """Academic focus - for educational content"""
        return cls(enabled=True, strategies=['background', 'academic'])
    
    @classmethod
    def transcript_only(cls):
        """No enrichment - transcript only"""
        return cls(enabled=False, strategies=[])

# ==================== SOURCE TRACKING SYSTEM ====================

@dataclass
class SourceContribution:
    """Track which sources contributed to the answer"""
    source_type: str  # 'transcript', 'background', 'discussions', 'academic', 'current'
    content_preview: str  # First 200 chars
    relevance_score: float = 0.0
    used_in_context: bool = False
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class SourceTracker:
    """Track and analyze source contributions"""
    
    def __init__(self):
        self.sources: List[SourceContribution] = []
        self.query_history: List[Dict] = []
    
    def add_source(self, source_type: str, content: str, relevance: float = 0.0):
        """Add a source to tracking"""
        preview = content[:200] + "..." if len(content) > 200 else content
        source = SourceContribution(
            source_type=source_type,
            content_preview=preview,
            relevance_score=relevance
        )
        self.sources.append(source)
    
    def mark_used(self, source_type: str):
        """Mark a source type as used in context"""
        for source in self.sources:
            if source.source_type == source_type:
                source.used_in_context = True
    
    def get_summary(self) -> Dict:
        """Get summary of source usage"""
        total = len(self.sources)
        used = sum(1 for s in self.sources if s.used_in_context)
        
        by_type = {}
        for source in self.sources:
            by_type[source.source_type] = by_type.get(source.source_type, 0) + 1
        
        return {
            'total_sources': total,
            'used_sources': used,
            'sources_by_type': by_type,
            'sources': [asdict(s) for s in self.sources]
        }
    
    def log_query(self, question: str, answer: str, sources_used: List[str]):
        """Log a query and its sources"""
        self.query_history.append({
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'answer_preview': answer[:200],
            'sources_used': sources_used
        })
    
    def export_report(self, filepath: str = "source_tracking_report.json"):
        """Export tracking data to JSON"""
        report = {
            'summary': self.get_summary(),
            'query_history': self.query_history,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Source tracking report saved to: {filepath}")
        return filepath

# ==================== CORE FUNCTIONS ====================

def extract_video_id(url: str):
    """Extract video ID from various YouTube URL formats"""
    try:
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        elif "youtube.com/watch" in url:
            parsed = urlparse(url)
            video_id = parse_qs(parsed.query).get('v')
            if video_id:
                return video_id[0]
        elif "youtube.com/embed/" in url:
            return url.split("youtube.com/embed/")[1].split("?")[0]
        raise ValueError("Could not extract video ID from URL")
    except Exception as e:
        raise ValueError(f"Invalid YouTube URL format: {str(e)}")

def extract_text_from_transcript(transcript_obj):
    """Extract text from FetchedTranscript object"""
    if hasattr(transcript_obj, 'snippets'):
        snippets = transcript_obj.snippets
        if isinstance(snippets, list) and len(snippets) > 0:
            texts = [snippet.text for snippet in snippets if hasattr(snippet, 'text')]
            if texts:
                return " ".join(texts)
    
    try:
        texts = [item.text for item in transcript_obj if hasattr(item, 'text')]
        if texts:
            return " ".join(texts)
    except:
        pass
    
    return str(transcript_obj)

def get_video_title_from_youtube(video_id: str):
    """Get video title directly from YouTube using yt-dlp"""
    try:
        import yt_dlp
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return info.get('title', f"YouTube Video {video_id}")
    except Exception as e:
        print(f"Could not fetch title from YouTube: {e}")
        return f"YouTube Video {video_id}"

def extract_key_topics(transcript: str, max_topics: int = 3) -> List[str]:
    """Extract key topics from transcript using keyword frequency"""
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                   'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                   'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                   'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                   'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
                   'who', 'when', 'where', 'why', 'how', 'so', 'than', 'too', 'very',
                   'just', 'now', 'get', 'got', 'like', 'know', 'think', 'going', 'want'}
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', transcript.lower())
    
    word_freq = {}
    for word in words:
        if word not in common_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_topics]]

# ==================== CONTENT ENRICHER ====================

class ContentEnricher:
    """Intelligent content enrichment with source tracking"""
    
    def __init__(self, config: EnrichmentConfig, source_tracker: Optional[SourceTracker] = None):
        self.config = config
        self.tracker = source_tracker or SourceTracker()
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.search = None
        
        if self.config.enabled and self.serper_api_key:
            try:
                os.environ["SERPER_API_KEY"] = self.serper_api_key
                self.search = GoogleSerperAPIWrapper()
                print("✓ Serper API initialized")
            except Exception as e:
                print(f"⚠ Serper API initialization failed: {e}")
                self.search = None
        else:
            if self.config.enabled and not self.serper_api_key:
                print("⚠ SERPER_API_KEY not found - web enrichment disabled")
    
    def _safe_search(self, query: str, source_type: str) -> str:
        """Perform safe search with tracking"""
        if not self.search:
            return ""
        
        try:
            results = self.search.run(query)
            truncated = results[:self.config.max_results_per_strategy] if results else ""
            
            # Track this source
            if self.config.track_sources and truncated:
                self.tracker.add_source(source_type, truncated, relevance=0.8)
            
            return truncated
        except Exception as e:
            print(f"  ✗ Search failed for '{query}': {e}")
            return ""
    
    def get_background_context(self, video_title: str, key_topics: List[str]) -> str:
        """Strategy 1: Get background information on key topics"""
        if not self.search or 'background' not in self.config.strategies:
            return ""
        
        print("  → [BACKGROUND] Fetching topic context...")
        context_parts = []
        
        for topic in key_topics[:2]:
            result = self._safe_search(f"{topic} overview explanation", "background")
            if result:
                context_parts.append(f"Background on '{topic}':\n{result}")
        
        return "\n\n".join(context_parts)
    
    def get_related_discussions(self, video_title: str) -> str:
        """Strategy 2: Find related discussions and analyses"""
        if not self.search or 'discussions' not in self.config.strategies:
            return ""
        
        print("  → [DISCUSSIONS] Searching for related content...")
        query = f'"{video_title}" discussion analysis review'
        return self._safe_search(query, "discussions")
    
    def get_academic_context(self, video_title: str, key_topics: List[str]) -> str:
        """Strategy 3: Search for academic or research context"""
        if not self.search or 'academic' not in self.config.strategies:
            return ""
        
        print("  → [ACADEMIC] Searching for research sources...")
        main_topic = key_topics[0] if key_topics else video_title
        query = f"{main_topic} research paper study academic"
        return self._safe_search(query, "academic")
    
    def get_current_info(self, video_title: str, key_topics: List[str]) -> str:
        """Strategy 4: Get current/recent information on topics"""
        if not self.search or 'current' not in self.config.strategies:
            return ""
        
        print("  → [CURRENT] Fetching latest information...")
        main_topic = key_topics[0] if key_topics else video_title
        query = f"{main_topic} latest 2025 updates news"
        return self._safe_search(query, "current")
    
    def enrich(self, video_title: str, transcript: str) -> Dict[str, str]:
        """Apply all configured enrichment strategies"""
        if not self.config.enabled or not self.search:
            print("Enrichment disabled or API unavailable")
            return {}
        
        print(f"\n🔍 Enriching content with strategies: {self.config.strategies}")
        
        # Extract key topics
        key_topics = extract_key_topics(transcript)
        print(f"  Key topics identified: {', '.join(key_topics)}")
        
        enriched_data = {}
        
        # Apply each strategy
        strategy_map = {
            'background': lambda: self.get_background_context(video_title, key_topics),
            'discussions': lambda: self.get_related_discussions(video_title),
            'academic': lambda: self.get_academic_context(video_title, key_topics),
            'current': lambda: self.get_current_info(video_title, key_topics)
        }
        
        for strategy in self.config.strategies:
            if strategy in strategy_map:
                result = strategy_map[strategy]()
                if result:
                    enriched_data[strategy] = result
        
        print(f"✓ Enrichment complete ({len(enriched_data)} sources added)\n")
        return enriched_data
    
    def get_tracker(self) -> SourceTracker:
        """Get the source tracker"""
        return self.tracker

# ==================== DOCUMENT LOADING ====================

def load_and_enrich_documents(url: str, config: Optional[EnrichmentConfig] = None, 
                              source_tracker: Optional[SourceTracker] = None) -> Tuple[List[str], Dict, SourceTracker]:
    """
    Load transcript and enrich with configured strategies
    Returns:
        - documents: List of enriched content
        - metadata: Video and enrichment metadata
        - source_tracker: Tracker with source information
    """
    if config is None:
        config = EnrichmentConfig.preset_balanced()
    
    if source_tracker is None:
        source_tracker = SourceTracker()
    
    try:
        video_id = extract_video_id(url)
        print(f"Extracted video ID: {video_id}")
        
        api = YouTubeTranscriptApi()
        transcript_obj = None
        full_transcript = None
        
        # Try to fetch transcript with multiple fallback strategies
        try:
            # Strategy 1: Try English transcript
            print("Attempting to fetch English transcript...")
            transcript_obj = api.fetch(video_id, languages=['en'])
            full_transcript = extract_text_from_transcript(transcript_obj)
            print(f"✓ Successfully fetched English transcript")
            
        except Exception as e1:
            print(f"English transcript not available: {e1}")
            
            try:
                # Strategy 2: Try fetching any available transcript
                print("Attempting to fetch any available transcript...")
                transcript_obj = api.fetch(video_id)
                full_transcript = extract_text_from_transcript(transcript_obj)
                print(f"✓ Successfully fetched default transcript")
                
            except Exception as e2:
                print(f"Default transcript fetch failed: {e2}")
                
                try:
                    # Strategy 3: List all available transcripts and get the first one
                    print("Attempting to list and fetch first available transcript...")
                    transcript_list = api.list(video_id)
                    
                    # TranscriptList is iterable but doesn't have len()
                    # Try to get the first available transcript
                    available_transcripts = list(transcript_list)
                    
                    if not available_transcripts:
                        raise Exception("No transcripts available for this video")
                    
                    # Try to find English or auto-generated transcript first
                    preferred_transcript = None
                    for transcript in available_transcripts:
                        if hasattr(transcript, 'language_code'):
                            if transcript.language_code in ['en', 'en-US', 'en-GB']:
                                preferred_transcript = transcript
                                break
                    
                    # If no English found, use first available
                    if preferred_transcript is None:
                        preferred_transcript = available_transcripts[0]
                    
                    # Fetch the selected transcript
                    transcript_obj = preferred_transcript.fetch()
                    full_transcript = extract_text_from_transcript(transcript_obj)
                    
                    language = getattr(preferred_transcript, 'language_code', 'unknown')
                    print(f"✓ Successfully fetched transcript in language: {language}")
                    
                except Exception as e3:
                    error_msg = (
                        f"Failed to fetch transcript for video {video_id}. "
                        f"Errors encountered:\n"
                        f"1. English transcript: {str(e1)}\n"
                        f"2. Default transcript: {str(e2)}\n"
                        f"3. List transcripts: {str(e3)}\n"
                        f"The video may not have any transcripts available."
                    )
                    raise Exception(error_msg)
        
        # Validate transcript content
        if not full_transcript or not full_transcript.strip():
            raise Exception("Transcript was fetched but contains no text content")
        
        print(f"Successfully extracted transcript ({len(full_transcript)} characters)")
        
        # Track transcript as primary source
        source_tracker.add_source('transcript', full_transcript, relevance=1.0)
        source_tracker.mark_used('transcript')
        
        # Get video title
        video_title = get_video_title_from_youtube(video_id)
        print(f"Video title: {video_title}")
        
        metadata = {
            'title': video_title,
            'video_id': video_id,
            'source': url,
            'config': config.to_dict(),
            'processing_timestamp': datetime.now().isoformat()
        }
        
        # Start with transcript
        content_parts = [f"=== VIDEO TRANSCRIPT ===\n{full_transcript}"]
        
        # Apply enrichment if configured
        if config.enabled:
            enricher = ContentEnricher(config, source_tracker)
            enriched_data = enricher.enrich(video_title, full_transcript)
            
            for strategy, data in enriched_data.items():
                content_parts.append(f"\n\n=== WEB CONTEXT: {strategy.upper()} ===\n{data}")
                source_tracker.mark_used(strategy)
            
            metadata['enrichment_sources'] = list(enriched_data.keys())
        else:
            print("Using transcript only (enrichment disabled)")
            metadata['enrichment_sources'] = []
        
        enriched_content = "\n".join(content_parts)
        
        return [enriched_content], metadata, source_tracker
        
    except Exception as e:
        raise Exception(f"Failed to load and process video: {str(e)}")
# ==================== VECTOR STORE ====================

def create_vector_store(documents: list):
    """Create FAISS vector store with metadata"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    text_chunks = text_splitter.create_documents(documents)
    print(f"Created {len(text_chunks)} text chunks")
    
    embeddings = None
    
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        print("Using HuggingFace embeddings (local)...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    except ImportError:
        print("HuggingFace not available, trying alternatives...")
        
        try:
            from langchain_community.embeddings import OllamaEmbeddings
            print("Using Ollama embeddings (local)...")
            embeddings = OllamaEmbeddings(model="llama2")
        except:
            print("Using simple embeddings (fast but basic)...")
            embeddings = FakeEmbeddings(size=384)
    
    print("Creating vector store...")
    vector_store = FAISS.from_documents(text_chunks, embeddings)
    print("✓ Vector store created")
    
    return vector_store

# ==================== RAG CHAIN WITH SOURCE TRACKING ====================

class TrackedRAGChain:
    """RAG chain with source tracking capabilities"""
    
    def __init__(self, vector_store, metadata: dict, source_tracker: SourceTracker):
        self.vector_store = vector_store
        self.metadata = metadata
        self.tracker = source_tracker
        self.chain = self._create_chain()
    
    def _create_chain(self):
        """Create the RAG chain"""
        if not os.getenv("GROQ_API_KEY"):
            raise Exception("GROQ_API_KEY not found!")
        
        print("Using Groq LLM (free & fast)")
        
        models_to_try = [
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        
        llm = None
        for model in models_to_try:
            try:
                llm = ChatGroq(
                    model_name=model,
                    temperature=0,
                    groq_api_key=os.getenv("GROQ_API_KEY")
                )
                print(f"Using model: {model}")
                break
            except Exception as e:
                print(f"Model {model} not available: {e}")
                continue
        
        if not llm:
            raise Exception("No Groq models available")
        
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 6}
        )
        
        enrichment_note = ""
        if self.metadata.get('config', {}).get('enabled'):
            strategies = ', '.join(self.metadata.get('enrichment_sources', []))
            if strategies:
                enrichment_note = f"\n\nNOTE: Context includes video transcript + web enrichment ({strategies})."
        
        prompt_template = f"""You are an expert assistant analyzing YouTube video content.

SOURCES IN CONTEXT:
1. VIDEO TRANSCRIPT (primary source - most reliable)
2. WEB CONTEXT (background, discussions, research - supporting info){enrichment_note}

INSTRUCTIONS:
- Answer based on the context below
- Prioritize transcript information
- Use web context for additional background
- If info not in context, state clearly
- Cite source type when relevant (e.g., "According to the transcript..." or "Web sources suggest...")

CONTEXT:
{{context}}

QUESTION:
{{question}}

ANSWER:"""
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        return (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
    
    def invoke(self, question: str) -> str:
        """Invoke the chain and track sources"""
        answer = self.chain.invoke(question)
        
        # Identify which sources were likely used
        sources_used = ['transcript']  # Always uses transcript
        if self.metadata.get('enrichment_sources'):
            sources_used.extend(self.metadata['enrichment_sources'])
        
        # Log the query
        self.tracker.log_query(question, answer, sources_used)
        
        return answer
    
    def invoke_with_sources(self, question: str) -> Dict:
        """Invoke and return answer with source information"""
        answer = self.invoke(question)
        
        return {
            'answer': answer,
            'sources_summary': self.tracker.get_summary(),
            'metadata': self.metadata
        }

# ==================== HELPER FUNCTIONS ====================

def print_config_options():
    """Print available configuration presets"""
    print("\n" + "="*60)
    print("ENRICHMENT CONFIGURATION PRESETS")
    print("="*60)
    
    presets = {
        '1. Transcript Only': EnrichmentConfig.transcript_only(),
        '2. Minimal': EnrichmentConfig.preset_minimal(),
        '3. Balanced (Recommended)': EnrichmentConfig.preset_balanced(),
        '4. Comprehensive': EnrichmentConfig.preset_comprehensive(),
        '5. Academic': EnrichmentConfig.preset_academic()
    }
    
    for name, config in presets.items():
        print(f"\n{name}:")
        print(f"  Enabled: {config.enabled}")
        print(f"  Strategies: {config.strategies}")
        print(f"  Track Sources: {config.track_sources}")
    
    print("\n" + "="*60 + "\n")

def create_rag_system(url: str, config: Optional[EnrichmentConfig] = None):
    """
    Create complete RAG system with tracking
    
    Returns:
        - rag_chain: TrackedRAGChain for asking questions
        - source_tracker: SourceTracker for analysis
        - metadata: Video and enrichment metadata
    """
    if config is None:
        config = EnrichmentConfig.preset_balanced()
    
    print(f"\n{'='*60}")
    print(f"CREATING RAG SYSTEM")
    print(f"Configuration: {config.strategies if config.enabled else 'Transcript Only'}")
    print(f"{'='*60}\n")
    
    # Load and enrich
    docs, metadata, tracker = load_and_enrich_documents(url, config)
    
    # Create vector store
    vector_store = create_vector_store(docs)
    
    # Create RAG chain with tracking
    rag_chain = TrackedRAGChain(vector_store, metadata, tracker)
    
    print(f"\n{'='*60}")
    print("✓ RAG SYSTEM READY")
    print(f"{'='*60}\n")
    
    return rag_chain, tracker, metadata


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    """
    Example usage demonstrating all features
    """
    
    # Show available configurations
    print_config_options()
    
    # Example 1: Use preset configuration
    print("\n" + "="*60)
    print("EXAMPLE 1: Balanced Enrichment")
    print("="*60)
    
    config = EnrichmentConfig.preset_balanced()
    rag_chain, tracker, metadata = create_rag_system(
        "https://youtube.com/watch?v=...",
        config=config
    )
    
    # Ask questions
    answer = rag_chain.invoke("What is the main topic?")
    print(f"\nAnswer: {answer}")
    
    # Get source summary
    print("\nSource Summary:")
    print(json.dumps(tracker.get_summary(), indent=2))
    
    # Export tracking report
    tracker.export_report("source_report.json")
    
    
    # Example 2: Custom configuration
    print("\n" + "="*60)
    print("EXAMPLE 2: Custom Configuration")
    print("="*60)
    
    custom_config = EnrichmentConfig(
        enabled=True,
        strategies=['background', 'current'],
        max_results_per_strategy=800,
        track_sources=True
    )
    
    rag_chain2, tracker2, metadata2 = create_rag_system(
        "https://youtube.com/watch?v=...",
        config=custom_config
    )
    
    # Ask with source details
    result = rag_chain2.invoke_with_sources("Explain the key concepts")
    print(f"\nAnswer: {result['answer']}")
    print(f"\nSources: {result['sources_summary']['sources_by_type']}")