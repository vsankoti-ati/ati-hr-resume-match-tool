"""
HR Resume Match Tool - Streamlit Application
Main application interface for resume matching analysis
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import logging
import re
from datetime import datetime
from app.matcher import get_matching_engine
from utils.report_generator import generate_pdf_report
from config.config import Config
from app.auth_wrapper import require_authentication, display_logout_button, get_current_user
from utils.health_check import check_ollama_health, get_model_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="HR Resume Match Tool",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f497d;
        text-align: center;
        padding: 1rem 0;
    }
    .match-score {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .match-excellent { color: #28a745; background-color: #d4edda; }
    .match-good { color: #ffc107; background-color: #fff3cd; }
    .match-fair { color: #fd7e14; background-color: #ffe5cc; }
    .match-poor { color: #dc3545; background-color: #f8d7da; }
    .section-header {
        font-size: 1.8rem;
        color: #1f497d;
        border-bottom: 2px solid #1f497d;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-success { background-color: #d4edda; border-left: 4px solid #28a745; }
    .info-warning { background-color: #fff3cd; border-left: 4px solid #ffc107; }
    .info-danger { background-color: #f8d7da; border-left: 4px solid #dc3545; }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'profile_filename' not in st.session_state:
        st.session_state.profile_filename = None
    if 'jd_filename' not in st.session_state:
        st.session_state.jd_filename = None
    # Authentication-related session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'user_roles' not in st.session_state:
        st.session_state.user_roles = []
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'token_expiry' not in st.session_state:
        st.session_state.token_expiry = None


def get_candidate_name_from_filename(filename: str) -> str:
    """Extract and sanitize candidate name from profile filename"""
    name = Path(filename).stem
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    return name[:50] if len(name) > 50 else name or "candidate"


def display_match_score(percentage: float, grade: str):
    """Display match score with color coding"""
    if percentage >= Config.MATCH_THRESHOLD_EXCELLENT:
        score_class = "match-excellent"
    elif percentage >= Config.MATCH_THRESHOLD_GOOD:
        score_class = "match-good"
    elif percentage >= Config.MATCH_THRESHOLD_FAIR:
        score_class = "match-fair"
    else:
        score_class = "match-poor"
    
    st.markdown(f'<div class="match-score {score_class}">{percentage}%<br><small>{grade}</small></div>', 
                unsafe_allow_html=True)


def display_matching_skills(matching_skills: dict):
    """Display matching skills section"""
    st.markdown('<div class="section-header">🎯 Matching Skills & Qualifications</div>', 
                unsafe_allow_html=True)
    
    cols = st.columns(2)
    
    for idx, (category, skills) in enumerate(matching_skills.items()):
        if skills:
            with cols[idx % 2]:
                st.subheader(category.replace('_', ' ').title())
                for skill in skills:
                    st.markdown(f"✅ {skill}")


def display_detailed_matches(detailed_matches: list):
    """Display detailed match analysis"""
    st.markdown('<div class="section-header">🔍 Detailed Match Analysis</div>', 
                unsafe_allow_html=True)
    
    if not detailed_matches:
        st.info("No detailed matches to display")
        return
    
    for match in detailed_matches:
        with st.expander(f"{match.get('category', 'N/A')}: {match.get('item', 'N/A')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Profile Evidence:**")
                st.write(match.get('profile_evidence', 'N/A'))
            
            with col2:
                st.markdown("**JD Requirement:**")
                st.write(match.get('jd_requirement', 'N/A'))
            
            match_strength = match.get('match_strength', 'N/A')
            if match_strength == 'Strong':
                st.success(f"Match Strength: {match_strength}")
            elif match_strength == 'Moderate':
                st.warning(f"Match Strength: {match_strength}")
            else:
                st.info(f"Match Strength: {match_strength}")


def display_gaps(gaps: list):
    """Display gaps in profile"""
    st.markdown('<div class="section-header">⚠️ Skills & Qualifications Gaps</div>', 
                unsafe_allow_html=True)
    
    if not gaps:
        st.success("No significant gaps identified! 🎉")
        return
    
    for gap in gaps:
        importance = gap.get('importance', 'N/A')
        
        if importance == 'Critical':
            st.error(f"**{importance}**: {gap.get('requirement', 'N/A')}")
        elif importance == 'Important':
            st.warning(f"**{importance}**: {gap.get('requirement', 'N/A')}")
        else:
            st.info(f"**{importance}**: {gap.get('requirement', 'N/A')}")
        
        st.markdown(f"💡 **Suggestion:** {gap.get('suggestion', 'N/A')}")
        st.markdown(f"⏱️ **Timeline:** {gap.get('timeline', 'N/A')}")
        st.markdown("---")


def display_strengths(strengths: list):
    """Display profile strengths"""
    st.markdown('<div class="section-header">💪 Profile Strengths & Highlights</div>', 
                unsafe_allow_html=True)
    
    if not strengths:
        st.info("No specific strengths highlighted")
        return
    
    for strength in strengths:
        st.success(f"**{strength.get('skill_or_experience', 'N/A')}**")
        st.markdown(f"📌 **Relevance:** {strength.get('relevance_to_jd', 'N/A')}")
        st.markdown(f"🎯 **How to Highlight:** {strength.get('highlight_strategy', 'N/A')}")
        st.markdown("---")


def display_anomalies(anomalies: list):
    """Display anomalies and discrepancies"""
    st.markdown('<div class="section-header">🚨 Anomalies & Discrepancies</div>', 
                unsafe_allow_html=True)
    
    if not anomalies:
        st.success("No anomalies detected! ✅")
        return
    
    for anomaly in anomalies:
        severity = anomaly.get('severity', 'N/A')
        
        if severity == 'High':
            st.error(f"**{severity} Severity** - {anomaly.get('type', 'N/A')}")
        elif severity == 'Medium':
            st.warning(f"**{severity} Severity** - {anomaly.get('type', 'N/A')}")
        else:
            st.info(f"**{severity} Severity** - {anomaly.get('type', 'N/A')}")
        
        st.markdown(f"📝 **Description:** {anomaly.get('description', 'N/A')}")
        st.markdown(f"💡 **Recommendation:** {anomaly.get('recommendation', 'N/A')}")
        st.markdown("---")


def display_recommendations(recommendations: dict):
    """Display recommendations"""
    st.markdown('<div class="section-header">💡 Recommendations</div>', 
                unsafe_allow_html=True)
    
    for category, recs in recommendations.items():
        if recs:
            st.subheader(category.replace('_', ' ').title())
            for rec in recs:
                st.markdown(f"• {rec}")


def main():
    """Main application function"""
    initialize_session_state()
    
    # Check authentication
    if not require_authentication():
        return  # require_authentication will handle rendering login page
    
    # Check Ollama health (blocking check on startup)
    is_healthy, health_message, health_details = check_ollama_health()
    
    if not is_healthy:
        st.error(f"**🔧 AI Service Status:** {health_message}")
        st.warning("""
        **The AI service is not ready yet.**
        
        This typically happens on first startup when:
        - Ollama service is initializing (30-60 seconds)
        - Models are being downloaded/loaded (2-5 minutes on first run)
        - GPU is being allocated (Azure Container Apps with serverless GPU)
        - Model is loading into GPU memory (30-60 seconds)
        
        Please wait a moment and click the button below to retry.
        """)
        
        # Show detailed status
        st.info("**Current Status:**")
        col1, col2 = st.columns(2)
        with col1:
            if health_details.get('reachable'):
                st.success("✅ Ollama Service: Running")
            else:
                st.error("❌ Ollama Service: Not Running")
                
            if health_details.get('model_available'):
                st.success(f"✅ Model '{Config.OLLAMA_MODEL_NAME}': Loaded")
            else:
                st.error(f"❌ Model '{Config.OLLAMA_MODEL_NAME}': Not Loaded")
        
        with col2:
            if health_details.get('inference_ready'):
                st.success("✅ Inference: Working")
            else:
                st.error("❌ Inference: Not Working")
                
            response_time = health_details.get('response_time_ms')
            if response_time:
                st.info(f"⏱️ Response Time: {response_time}ms")
        
        # Show error details if available
        if health_details.get('error'):
            with st.expander("🔍 Error Details"):
                st.code(health_details['error'], language=None)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Retry Connection", type="primary"):
                st.rerun()
        
        st.stop()
    
    # Header
    st.markdown('<div class="main-header">📄 HR Resume Match Tool</div>', 
                unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        # Display user info and logout button
        display_logout_button()
        
        st.header("About")
        st.info("""
        This tool uses AI to match candidate profiles against job descriptions.
        
        **Features:**
        - Overall match percentage
        - Detailed skill matching
        - Gap analysis
        - Profile strengths
        - Anomaly detection
        - PDF report export
        """)
        
        st.header("Model Info")
        st.text(f"Model: {Config.OLLAMA_MODEL_NAME}")
        st.text(f"Ollama URL: {Config.OLLAMA_BASE_URL}")
        
        # Live system health status
        st.markdown("---")
        st.subheader("🏥 System Health")
        
        # Get current health status
        is_healthy, health_msg, health_details = check_ollama_health()
        
        if is_healthy:
            st.success(health_msg)
            response_time = health_details.get('response_time_ms', 0)
            st.metric("Inference Time", f"{response_time}ms", 
                     help="Time to generate response from model")
            
            # Show status indicators
            col1, col2 = st.columns(2)
            with col1:
                st.caption("🟢 Service: Running")
                st.caption("🟢 Model: Loaded")
            with col2:
                st.caption("🟢 GPU: Active" if response_time < 5000 else "🟡 CPU: Active")
                st.caption("🟢 Inference: Ready")
            
            # Show loaded models
            model_info = get_model_info()
            if model_info.get('model_count', 0) > 0:
                with st.expander("📦 Loaded Models"):
                    for model in model_info.get('models', []):
                        st.text(f"• {model['name']}")
                        st.caption(f"  Size: {model['size_gb']:.2f} GB")
        else:
            st.error(health_msg)
            
            # Detailed status
            col1, col2 = st.columns(2)
            with col1:
                if health_details.get('reachable'):
                    st.caption("🟢 Service: Running")
                else:
                    st.caption("🔴 Service: Not Running")
                    
                if health_details.get('model_available'):
                    st.caption("🟢 Model: Loaded")
                else:
                    st.caption("🔴 Model: Not Loaded")
            
            with col2:
                if health_details.get('inference_ready'):
                    st.caption("🟢 Inference: Ready")
                else:
                    st.caption("🔴 Inference: Failed")
                    
                response_time = health_details.get('response_time_ms')
                if response_time:
                    st.caption(f"⏱️ Time: {response_time}ms")
            
            # Show error details if available
            if health_details.get('error'):
                with st.expander("🔍 Error Details"):
                    st.code(health_details['error'], language=None)
        
        # Manual refresh button
        if st.button("🔄 Refresh Status"):
            st.rerun()
    
    # Main content area
    tab1, tab2 = st.tabs(["📤 Upload & Analyze", "📊 Results"])
    
    with tab1:
        st.header("Upload Documents")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Candidate Profile")
            profile_file = st.file_uploader(
                "Upload resume (PDF or Word)",
                type=['pdf', 'docx', 'doc'],
                key='profile',
                help="Maximum file size: 200MB"
            )
            
            if profile_file:
                st.success(f"✅ {profile_file.name} ({profile_file.size / 1024:.1f} KB)")
        
        with col2:
            st.subheader("Job Description")
            jd_file = st.file_uploader(
                "Upload job description (PDF or Word)",
                type=['pdf', 'docx', 'doc'],
                key='jd',
                help="Maximum file size: 200MB"
            )
            
            if jd_file:
                st.success(f"✅ {jd_file.name} ({jd_file.size / 1024:.1f} KB)")
        
        st.markdown("---")
        
        # Analyze button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button(
                "🚀 Analyze Match",
                type="primary",
                disabled=not (profile_file and jd_file),
                use_container_width=True
            )
        
        if analyze_button:
            st.session_state.analysis_complete = False
            st.session_state.analysis_result = None
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Initialize engine
                status_text.text("Initializing analysis engine...")
                progress_bar.progress(10)
                engine = get_matching_engine()
                
                # Step 2: Check system health
                status_text.text("Checking system health...")
                progress_bar.progress(20)
                is_healthy, msg = engine.check_system_health()
                if not is_healthy:
                    st.error(f"System health check failed: {msg}")
                    st.stop()
                
                # Step 3: Read files
                status_text.text("Reading uploaded files...")
                progress_bar.progress(30)
                profile_bytes = profile_file.read()
                jd_bytes = jd_file.read()
                
                # Step 4: Process match request
                status_text.text("Parsing documents and analyzing match...")
                progress_bar.progress(40)
                
                with st.spinner("This may take 30-60 seconds depending on document size..."):
                    analysis_result, error = engine.process_match_request(
                        profile_bytes, profile_file.name,
                        jd_bytes, jd_file.name
                    )
                
                if error:
                    st.error(f"Analysis failed: {error}")
                    st.stop()
                
                # Step 5: Save results
                status_text.text("Analysis complete! Preparing results...")
                progress_bar.progress(100)
                
                st.session_state.analysis_result = analysis_result
                st.session_state.analysis_complete = True
                st.session_state.profile_filename = profile_file.name
                st.session_state.jd_filename = jd_file.name
                
                st.success("✅ Analysis completed successfully!")
                st.balloons()
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Automatically switch to results tab
                st.info("👉 Switch to the 'Results' tab to view the analysis")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Analysis error: {str(e)}", exc_info=True)
    
    with tab2:
        if not st.session_state.analysis_complete or not st.session_state.analysis_result:
            st.info("📤 Please upload documents and run analysis first")
            return
        
        result = st.session_state.analysis_result
        
        # Overall match score
        st.header("Overall Match Score")
        percentage = result.get('overall_match_percentage', 0)
        engine = get_matching_engine()
        grade = engine.get_match_grade(percentage)
        display_match_score(percentage, grade)
        
        # Summary
        st.markdown("### Summary")
        st.write(result.get('match_summary', 'No summary available'))
        
        # Metadata
        with st.expander("📋 Document Information"):
            metadata = result.get('metadata', {})
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Profile:** {metadata.get('profile_filename', 'N/A')}")
                st.write(f"**Word Count:** {metadata.get('profile_word_count', 'N/A')}")
            with col2:
                st.write(f"**Job Description:** {metadata.get('jd_filename', 'N/A')}")
                st.write(f"**Word Count:** {metadata.get('jd_word_count', 'N/A')}")
        
        st.markdown("---")
        
        # Display all sections
        display_matching_skills(result.get('matching_skills', {}))
        display_detailed_matches(result.get('detailed_matches', []))
        display_gaps(result.get('gaps_in_profile', []))
        display_strengths(result.get('profile_strengths', []))
        display_anomalies(result.get('anomalies', []))
        display_recommendations(result.get('recommendations', {}))
        
        # Export to PDF
        st.markdown("---")
        st.header("📥 Export Report")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📄 Download PDF Report", type="primary", use_container_width=True):
                with st.spinner("Generating PDF report..."):
                    try:
                        pdf_bytes = generate_pdf_report(result)
                        
                        if pdf_bytes:
                            # Get candidate name from metadata
                            metadata = result.get('metadata', {})
                            profile_filename = metadata.get('profile_filename', 'candidate')
                            candidate_name = get_candidate_name_from_filename(profile_filename)
                            filename = f"{candidate_name}_scorecard.pdf"
                            
                            st.download_button(
                                label="⬇️ Download Report",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("PDF report generated successfully!")
                        else:
                            st.error("Failed to generate PDF report")
                            
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        logger.error(f"PDF generation error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
