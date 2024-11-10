# white_paper_creator.py
import streamlit as st
from langchain_openai import ChatOpenAI
import yaml
from typing import List, Dict
import json
import re

class WhitePaperCreator:
    def __init__(self, api_key: str):
        self.model = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            api_key=api_key
        )
        
    def generate_title_suggestions(self, topic: str, target_audience: str) -> List[str]:
        """Generate title suggestions based on topic and target audience."""
        prompt = f"""Generate 5 compelling white paper titles for the following:
        Topic: {topic}
        Target Audience: {target_audience}
        
        Make the titles attention-grabbing and professional. Each title should be on a new line.
        """
        response = self.model.predict(prompt)
        return [title.strip() for title in response.split('\n') if title.strip()]
    
    def suggest_sections(self, title: str, topic: str) -> List[Dict]:
        """Suggest sections for the white paper."""
        prompt = f"""You are an expert at creating outlines for white papers. 
        Create a detailed outline with sections for a white paper with the following details:
        
        Title: {title}
        Topic: {topic}
        
        Respond ONLY with a JSON object in the following format, nothing else:
        {{
            "sections": [
                {{"name": "Executive Summary", "description": "Brief overview of the white paper's key points and findings"}},
                {{"name": "Introduction", "description": "Background information and context of the topic"}},
                {{"name": "Market Overview", "description": "Analysis of current market conditions and trends"}},
                {{"name": "Key Challenges", "description": "Discussion of main industry challenges and pain points"}},
                {{"name": "Solution Framework", "description": "Detailed explanation of proposed solutions and approaches"}},
                {{"name": "Implementation Strategy", "description": "Step-by-step guide for implementing the solutions"}},
                {{"name": "Conclusion", "description": "Summary of key takeaways and call to action"}}
            ]
        }}
        
        Use the example format above but create your own unique sections and descriptions relevant to the topic.
        The response must be valid JSON that can be parsed by Python's json.loads().
        Do not include any other text, only the JSON object."""
        
        try:
            response = self.model.predict(prompt)
            # Clean the response - remove any markdown formatting if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse the JSON
            data = json.loads(response)
            return data['sections']
        except json.JSONDecodeError as e:
            st.error(f"Error parsing sections. Using default template.")
            # Return a default template if JSON parsing fails
            return [
                {"name": "Executive Summary", "description": "Overview of key points and findings"},
                {"name": "Introduction", "description": f"Introduction to {topic}"},
                {"name": "Current State", "description": "Analysis of current situation"},
                {"name": "Challenges", "description": "Key challenges and problems"},
                {"name": "Solutions", "description": "Proposed solutions and approaches"},
                {"name": "Implementation", "description": "How to implement the solutions"},
                {"name": "Conclusion", "description": "Summary and next steps"}
            ]
    
    def generate_draft(self, title: str, sections: List[Dict], key_points: str) -> str:
        """Generate the initial draft of the white paper."""
        sections_text = "\n".join([f"- {s['name']}: {s['description']}" for s in sections])
        prompt = f"""Write a professional white paper with the following:
        Title: {title}
        
        Sections:
        {sections_text}
        
        Key Points to Include:
        {key_points}
        
        Write in a persuasive but professional tone. Include relevant statistics and concrete examples.
        Format in Markdown with proper headings and paragraphs."""
        
        return self.model.predict(prompt)
    
    def revise_draft(self, current_draft: str, feedback: str) -> str:
        """Revise the draft based on feedback."""
        prompt = f"""Revise this white paper based on the following feedback:
        
        Current Draft:
        {current_draft}
        
        Feedback to Incorporate:
        {feedback}
        
        Maintain the professional tone and formatting while addressing the feedback.
        Return the complete revised draft in Markdown format."""
        
        return self.model.predict(prompt)

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'stage' not in st.session_state:
        st.session_state.stage = 'topic'
    if 'title' not in st.session_state:
        st.session_state.title = ''
    if 'topic' not in st.session_state:
        st.session_state.topic = ''
    if 'audience' not in st.session_state:
        st.session_state.audience = ''
    if 'sections' not in st.session_state:
        st.session_state.sections = []
    if 'draft' not in st.session_state:
        st.session_state.draft = ''
    if 'title_suggestions' not in st.session_state:
        st.session_state.title_suggestions = []

def handle_title_selection(title: str, creator: WhitePaperCreator):
    """Handle the selection of a title and transition to sections stage."""
    try:
        st.session_state.title = title
        st.session_state.sections = creator.suggest_sections(
            title, st.session_state.topic)
        st.session_state.stage = 'sections'
    except Exception as e:
        st.error(f"An error occurred while generating sections: {str(e)}")

def main():
    st.set_page_config(page_title="White Paper Creator", layout="wide")
    
    with st.sidebar:
        api_key = st.text_input("Enter OpenAI API Key:", type="password")
        if not api_key:
            st.warning("Please enter your OpenAI API key to continue.")
            st.stop()
    
    creator = WhitePaperCreator(api_key)
    
    # Initialize session state
    initialize_session_state()
    
    st.title("White Paper Creator")
    
    # Progress indicator
    progress_options = ['Topic', 'Title', 'Sections', 'Draft']
    current_stage = st.session_state.stage
    current_index = progress_options.index(current_stage.capitalize()) if current_stage != 'topic' else 0
    st.progress(current_index / (len(progress_options) - 1))
    
    # Topic Input Stage
    if st.session_state.stage == 'topic':
        st.header("Step 1: Define Your White Paper")
        topic = st.text_area(
            "What's your white paper about? (Describe the main topic and goals)", 
            value=st.session_state.topic,
            height=100,
            help="Provide a clear description of your topic and what you want to achieve with this white paper"
        )
        audience = st.text_input(
            "Who is your target audience?", 
            value=st.session_state.audience,
            help="Specify your target audience (e.g., C-level executives, IT professionals, business owners)"
        )
        
        if st.button("Generate Title Suggestions", type="primary"):
            if topic and audience:
                with st.spinner('Generating title suggestions...'):
                    st.session_state.topic = topic
                    st.session_state.audience = audience
                    st.session_state.title_suggestions = creator.generate_title_suggestions(topic, audience)
                    st.session_state.stage = 'title'
                    st.rerun()
            else:
                st.warning("Please fill in both topic and target audience.")
    
    # Title Selection Stage
    elif st.session_state.stage == 'title':
        st.header("Step 2: Select Your Title")
        st.write("Topic:", st.session_state.topic)
        st.write("Target Audience:", st.session_state.audience)
        
        for title in st.session_state.title_suggestions:
            if st.button(f"Select: {title}", key=title):
                with st.spinner('Generating sections...'):
                    handle_title_selection(title, creator)
                    st.rerun()
        
        if st.button("← Back to Topic", key="back_to_topic"):
            st.session_state.stage = 'topic'
            st.rerun()
    
    # Section Review Stage
    elif st.session_state.stage == 'sections':
        st.header("Step 3: Review and Customize Sections")
        st.subheader(st.session_state.title)
        
        sections = []
        for i, section in enumerate(st.session_state.sections):
            with st.expander(f"Section {i+1}: {section['name']}", expanded=True):
                section_name = st.text_input(
                    "Section Name", 
                    value=section['name'],
                    key=f"name_{i}"
                )
                section_desc = st.text_area(
                    "Description", 
                    value=section['description'],
                    height=100,
                    key=f"desc_{i}"
                )
                sections.append({"name": section_name, "description": section_desc})
        
        st.write("---")
        key_points = st.text_area(
            "Additional key points to include:", 
            height=150,
            help="Add any specific points, data, or examples you want to include in the white paper"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Title Selection", key="back_to_title"):
                st.session_state.stage = 'title'
                st.rerun()
        with col2:
            if st.button("Generate Draft", type="primary", key="generate_draft"):
                with st.spinner('Generating draft...'):
                    st.session_state.draft = creator.generate_draft(
                        st.session_state.title, sections, key_points)
                    st.session_state.stage = 'draft'
                    st.rerun()
    
    # Draft Review Stage
    elif st.session_state.stage == 'draft':
        st.header("Step 4: Review and Refine Draft")
        
        # Add tabs for viewing and editing
        tab1, tab2 = st.tabs(["Preview", "Edit"])
        
        with tab1:
            st.markdown(st.session_state.draft)
            
        with tab2:
            feedback = st.text_area(
                "Enter your feedback for revision:", 
                height=150,
                help="Describe any changes you'd like to make to the draft"
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("← Back to Sections", key="back_to_sections"):
                    st.session_state.stage = 'sections'
                    st.rerun()
            
            with col2:
                if st.button("Revise Draft", key="revise_draft") and feedback:
                    with st.spinner('Revising draft...'):
                        st.session_state.draft = creator.revise_draft(
                            st.session_state.draft, feedback)
                        st.rerun()
            
            with col3:
                if st.download_button(
                    label="Download White Paper",
                    data=st.session_state.draft,
                    file_name="white_paper.md",
                    mime="text/markdown"
                ):
                    st.success("White paper downloaded successfully!")

if __name__ == "__main__":
    main()