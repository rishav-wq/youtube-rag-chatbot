import streamlit as st
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Import from youtube_rag.py (your main module)
from src.rag_pipeline import (
    EnrichmentConfig,
    create_rag_system,
    SourceTracker
)

def main():
    load_dotenv()
    
    st.set_page_config(
        page_title="YouTube RAG Chatbot Pro",
        page_icon="🎥",
        layout="wide"
    )
    
    # Custom CSS for better UI
    st.markdown("""
        <style>
        .source-box {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
        }
        .metric-card {
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🎥 YouTube RAG Chatbot Pro")
    st.markdown("*Advanced RAG with intelligent web enrichment and source tracking*")
    
    # Initialize session state
    if 'rag_chain' not in st.session_state:
        st.session_state.rag_chain = None
        st.session_state.tracker = None
        st.session_state.metadata = None
        st.session_state.chat_history = []
        st.session_state.auto_qa = []
        st.session_state.summaries = {}
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Check API keys
        groq_key = os.getenv("GROQ_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        
        st.subheader("API Status")
        st.write("✅ Groq API" if groq_key else "❌ Groq API (Required)")
        st.write("✅ Serper API" if serper_key else "⚠️ Serper API (Optional)")
        
        if not groq_key:
            st.error("GROQ_API_KEY not found! Get it at https://console.groq.com")
        
        st.markdown("---")
        
        # Enrichment preset selection
        st.subheader("🔍 Enrichment Mode")
        
        preset_options = {
            "Transcript Only (Fastest)": "transcript_only",
            "Minimal (Background)": "minimal",
            "Balanced (Recommended)": "balanced",
            "Comprehensive (All Sources)": "comprehensive",
            "Academic (Research Focus)": "academic"
        }
        
        selected_preset = st.selectbox(
            "Choose preset:",
            options=list(preset_options.keys()),
            index=2  # Default to Balanced
        )
        
        preset_key = preset_options[selected_preset]
        
        # Show what this preset includes
        preset_info = {
            "transcript_only": {"strategies": [], "desc": "Video transcript only - fastest and most accurate to video content"},
            "minimal": {"strategies": ["background"], "desc": "Adds basic background context"},
            "balanced": {"strategies": ["background", "discussions"], "desc": "Best balance of accuracy and context"},
            "comprehensive": {"strategies": ["background", "discussions", "academic", "current"], "desc": "Most thorough, includes all sources"},
            "academic": {"strategies": ["background", "academic"], "desc": "Focus on research and scholarly sources"}
        }
        
        with st.expander("ℹ️ What's included?"):
            info = preset_info[preset_key]
            st.write(info["desc"])
            if info["strategies"]:
                st.write("**Enrichment strategies:**")
                for strategy in info["strategies"]:
                    st.write(f"• {strategy.title()}")
        
        st.markdown("---")
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            custom_strategies = st.multiselect(
                "Custom strategies:",
                ["background", "discussions", "academic", "current"],
                default=preset_info[preset_key]["strategies"]
            )
            
            max_results = st.slider(
                "Max results per strategy:",
                500, 2000, 1000, 100
            )
            
            use_custom = st.checkbox("Use custom config")
        
        # Show current system status
        if st.session_state.rag_chain:
            st.markdown("---")
            st.success("✅ System Ready")
            if st.session_state.metadata:
                st.write(f"**Video:** {st.session_state.metadata.get('title', 'Unknown')[:50]}...")
                
                config = st.session_state.metadata.get('config', {})
                if config.get('enabled'):
                    st.write(f"**Sources:** {len(config.get('strategies', []))} active")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        youtube_url = st.text_input(
            "📺 Enter YouTube URL:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video URL"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        process_button = st.button("🚀 Process Video", type="primary", use_container_width=True)
    
    # Clear button
    if st.session_state.rag_chain:
        if st.button("🔄 Clear & Start Over"):
            st.session_state.rag_chain = None
            st.session_state.tracker = None
            st.session_state.metadata = None
            st.session_state.chat_history = []
            st.session_state.auto_qa = []
            st.session_state.summaries = {}
            st.rerun()
    
    # Process video
    if process_button:
        if not youtube_url:
            st.warning("⚠️ Please enter a YouTube URL")
        elif not groq_key:
            st.error("❌ GROQ_API_KEY is required!")
        else:
            # Create config based on selection
            if use_custom:
                config = EnrichmentConfig(
                    enabled=len(custom_strategies) > 0,
                    strategies=custom_strategies,
                    max_results_per_strategy=max_results,
                    track_sources=True
                )
            else:
                config_map = {
                    "transcript_only": EnrichmentConfig.transcript_only(),
                    "minimal": EnrichmentConfig.preset_minimal(),
                    "balanced": EnrichmentConfig.preset_balanced(),
                    "comprehensive": EnrichmentConfig.preset_comprehensive(),
                    "academic": EnrichmentConfig.preset_academic()
                }
                config = config_map[preset_key]
            
            # Process with progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("📥 Step 1/4: Fetching transcript...")
                progress_bar.progress(25)
                
                status_text.text("🔍 Step 2/4: Enriching content...")
                progress_bar.progress(50)
                
                # Create RAG system
                rag_chain, tracker, metadata = create_rag_system(youtube_url, config)
                
                status_text.text("🧠 Step 3/4: Creating embeddings...")
                progress_bar.progress(75)
                
                status_text.text("✨ Step 4/4: Building RAG chain...")
                progress_bar.progress(100)
                
                # Store in session
                st.session_state.rag_chain = rag_chain
                st.session_state.tracker = tracker
                st.session_state.metadata = metadata
                st.session_state.chat_history = []
                
                progress_bar.empty()
                status_text.empty()
                
                # Success message
                st.success(f"✅ Successfully processed: **{metadata['title']}**")
                
                # Show stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Sources Tracked", tracker.get_summary()['total_sources'])
                with col2:
                    sources = tracker.get_summary()['sources_by_type']
                    st.metric("📚 Source Types", len(sources))
                with col3:
                    enriched = "Yes" if config.enabled else "No"
                    st.metric("🔍 Enrichment", enriched)
                
                if config.enabled:
                    with st.expander("📋 View Source Details"):
                        st.json(tracker.get_summary()['sources_by_type'])
                
                st.success("✅ System ready! Use the sections below to generate summaries or ask questions.")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Error: {str(e)}")
                with st.expander("🔍 Show details"):
                    import traceback
                    st.code(traceback.format_exc())
    
    # Video Summaries Section (persistent, outside process_button block)
    if st.session_state.rag_chain:
        st.markdown("---")
        st.subheader("📝 Video Summaries")
        
        # Summary type selector
        summary_col1, summary_col2 = st.columns([3, 1])
        with summary_col1:
            summary_type = st.selectbox(
                "Choose summary type:",
                ["TL;DR (1-2 sentences)", "Brief (2-3 sentences)", 
                 "Bullet Points", "Detailed", "Comprehensive"],
                key="summary_type"
            )
        with summary_col2:
            st.write("")
            st.write("")
            generate_summary_btn = st.button("📝 Generate", key="gen_summary")
        
        # Map display names to internal types
        summary_type_map = {
            "TL;DR (1-2 sentences)": "tldr",
            "Brief (2-3 sentences)": "brief",
            "Bullet Points": "bullet_points",
            "Detailed": "detailed",
            "Comprehensive": "comprehensive"
        }
        
        # Generate summary on button click
        if generate_summary_btn:
            selected_type = summary_type_map[summary_type]
            with st.spinner(f"Generating {summary_type} summary..."):
                try:
                    summary = st.session_state.rag_chain.generate_summary(selected_type)
                    st.session_state.summaries[selected_type] = summary
                    st.success(f"✅ {summary_type} summary generated!")
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if "rate_limit" in error_msg.lower() or "429" in error_msg:
                        # Extract wait time if available
                        import re
                        wait_match = re.search(r'try again in ([\d\.]+[msh]+)', error_msg)
                        wait_time = wait_match.group(1) if wait_match else "a few minutes"
                        
                        st.error(f"⚠️ **Groq API Rate Limit Reached**")
                        st.warning(f"""
                        You've used up your daily token limit (100,000 tokens/day).
                        
                        **Wait time:** ~{wait_time}
                        
                        **Options:**
                        - ⏰ Wait for the limit to reset
                        - 💰 Upgrade at [Groq Console](https://console.groq.com/settings/billing)
                        - 💬 Continue using the chat (uses fewer tokens)
                        """)
                    else:
                        st.error(f"❌ Error: {error_msg}")
        
        # Display generated summaries
        if st.session_state.summaries:
            st.markdown("### Generated Summaries:")
            for stype, summary_data in st.session_state.summaries.items():
                type_display = {
                    'tldr': '⚡ TL;DR',
                    'brief': '📄 Brief',
                    'bullet_points': '📌 Bullet Points',
                    'detailed': '📖 Detailed',
                    'comprehensive': '📚 Comprehensive'
                }
                
                with st.expander(f"{type_display.get(stype, stype.title())} Summary", expanded=True):
                    st.markdown(summary_data['summary'])
                    st.caption(f"Generated at: {summary_data['generated_at']}")
        
        # Option to generate all summaries at once
        if st.button("📚 Generate All Summary Types", key="gen_all_summaries"):
            with st.spinner("Generating all summary types... This may take a minute."):
                try:
                    all_summaries = st.session_state.rag_chain.generate_all_summaries()
                    st.session_state.summaries = all_summaries
                    st.success("✅ All summaries generated!")
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if "rate_limit" in error_msg.lower() or "429" in error_msg:
                        st.error("⚠️ Rate limit reached! Please wait a few minutes and try again.")
                        st.info("💡 Tip: Generate one summary at a time to conserve tokens.")
                    else:
                        st.error(f"❌ Error: {error_msg}")
        
        # Auto Q&A Section (Optional)
        st.markdown("---")
        st.subheader("🤖 Auto-Generated Q&A")
        st.caption("⚠️ Note: This feature uses significant API tokens. Use sparingly if near rate limits.")
        
        qa_col1, qa_col2 = st.columns([3, 1])
        with qa_col1:
            num_questions = st.slider("Number of questions:", 1, 10, 5, key="num_qa")
        with qa_col2:
            st.write("")
            st.write("")
            generate_qa_btn = st.button("🤖 Generate Q&A", key="gen_qa")
        
        # Generate Q&A on button click
        if generate_qa_btn:
            with st.spinner(f"Generating {num_questions} questions and answers..."):
                try:
                    auto_qa = st.session_state.rag_chain.generate_auto_qa(num_questions=num_questions)
                    st.session_state.auto_qa = auto_qa
                    st.rerun()
                except Exception as e:
                    if "rate_limit" in str(e).lower():
                        st.error("⚠️ Rate limit reached! Please wait and try again later.")
                        st.info("💡 Your daily token limit has been exceeded. Try again in about 30 minutes, or reduce the number of questions.")
                    else:
                        st.error(f"Error generating Q&A: {str(e)}")
        
        # Display generated Q&A
        if st.session_state.auto_qa:
            st.markdown("### Generated Questions & Answers:")
            for i, qa in enumerate(st.session_state.auto_qa, 1):
                with st.expander(f"❓ {qa['question']}", expanded=(i==1)):
                    st.markdown(f"**Answer:** {qa['answer']}")
                    st.caption(f"Source: AI-generated based on video content")
    
    # Chat interface
    if st.session_state.rag_chain:
        st.markdown("---")
        st.header("💬 Ask Questions")
        
        # Display chat history
        for i, chat in enumerate(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**🤔 You:** {chat['question']}")
                st.markdown(f"**🤖 Assistant:** {chat['answer']}")
                if chat.get('sources'):
                    st.caption(f"📎 Sources: {', '.join(chat['sources'])}")
                st.markdown("---")
        
        # Question input
        user_question = st.text_input(
            "Your question:",
            key="question_input",
            placeholder="What is this video about?"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            ask_button = st.button("Ask", type="primary")
        with col2:
            if st.session_state.chat_history:
                if st.button("Clear Chat"):
                    st.session_state.chat_history = []
                    st.rerun()
        
        if ask_button and user_question:
            with st.spinner("🤔 Thinking..."):
                try:
                    # Get answer with source tracking
                    result = st.session_state.rag_chain.invoke_with_sources(user_question)
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'question': user_question,
                        'answer': result['answer'],
                        'sources': list(result['sources_summary']['sources_by_type'].keys()),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Analytics section (if system is active)
    if st.session_state.tracker and st.session_state.chat_history:
        st.markdown("---")
        st.header("📊 Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Query Statistics")
            st.metric("Total Questions", len(st.session_state.chat_history))
            
            summary = st.session_state.tracker.get_summary()
            st.metric("Sources Used", summary['used_sources'])
            st.metric("Source Types", len(summary['sources_by_type']))
        
        with col2:
            st.subheader("Source Breakdown")
            sources_by_type = st.session_state.tracker.get_summary()['sources_by_type']
            
            for source_type, count in sources_by_type.items():
                st.write(f"**{source_type.title()}:** {count}")
        
        # Export options
        st.subheader("📥 Export Data")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Source Report (JSON)"):
                st.session_state.tracker.export_report("source_report.json")
                st.success("✅ Exported to source_report.json")
        
        with col2:
            if st.button("Export Chat History (JSON)"):
                with open('chat_history.json', 'w') as f:
                    json.dump(st.session_state.chat_history, f, indent=2)
                st.success("✅ Exported to chat_history.json")
        
        with col3:
            if st.button("Export All Data"):
                # Export everything
                st.session_state.tracker.export_report("full_report.json")
                with open('chat_history.json', 'w') as f:
                    json.dump(st.session_state.chat_history, f, indent=2)
                st.success("✅ Exported all data!")

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>Built with Streamlit | Powered by Groq & Serper API</p>
            <p>Week 1-2: Smart Enrichment + Configuration + Source Tracking ✅</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()