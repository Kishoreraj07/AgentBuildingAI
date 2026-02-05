# video_to_word_converter.py 

import cv2
import os
import re
import docx
from datetime import datetime
import google.generativeai as genai
import json
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import config
import sys
import requests
from pathlib import Path
from typing import List, Dict, Tuple
import time
import random
import google.api_core.exceptions

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class VideoTranscriptAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the analyzer with Gemini API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-3-pro-preview")

        # Initialize the flowchart model
        self.flowchart_model = genai.GenerativeModel(model_name="gemini-flash-latest")

        self._last_video_path = ""
        self._frame_paths = []

    def clean_text_formatting(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'^\s*(SYSTEM|PROCESS_STEP|STEP_DESCRIPTION|ACTIONS):\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*\*', '', text)
        
        if not text.startswith('•') and '•The AI Agent' not in text:
            text = re.sub(r'^[•·○]\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*[•·○]\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'[•·○]+', '', text)
        
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = re.sub(r'[A-Z][a-z]+, [A-Z][a-z]+(?:\s*\(.*?)\)?', 'XXX, XXX', text)
        text = re.sub(r'MRN: \S+', 'MRN: XXX', text)
        text = re.sub(r'PMS: \S+', 'PMS: XXX', text)
        text = re.sub(r'(?<!mm/dd/)\d{2}/\d{2}/\d{4}', 'mm/dd/yyyy', text)
        text = re.sub(r'(VISA|Cash) \S+', r'\1 ****', text)
        text = re.sub(r'Assigned To" to "[^"]+"', 'Assigned To" to "XXX, XXX"', text)
        
        return text

    def extract_frames_from_video(self, video_path: str, output_dir: str = "frames",
                                method: str = "histogram",
                                crop_frames: bool = True,
                                crop_right_percent: float = 0.13,
                                hist_threshold: float = 0.08,
                                capture_interval_seconds: float = 0.2):

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"Video FPS: {fps}, Total frames: {total_frames}, Duration: {duration:.2f}s")
        print(f"Capture settings: Check every {capture_interval_seconds}s, threshold={hist_threshold}")
        
        frame_data = []
        frame_count = 0
        saved_count = 0
        prev_hist = None
        
        # REDUCED INTERVAL: Check more frequently (every 0.2 seconds instead of 0.5)
        frame_interval = int(fps * capture_interval_seconds)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                if crop_frames:
                    height, width = frame.shape[:2]
                    crop_width = int(width * (1 - crop_right_percent))
                    cropped_frame = frame[:, :crop_width]
                else:
                    cropped_frame = frame
                
                gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                
                if prev_hist is not None:
                    similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                    
                    if similarity < (1 - hist_threshold):
                        timestamp_sec = frame_count / fps
                        minutes = int(timestamp_sec // 60)
                        seconds = int(timestamp_sec % 60)
                        
                        frame_filename = f"frame_{minutes:02d}{seconds:02d}.jpg"
                        frame_path = os.path.join(output_dir, frame_filename)
                        
                        counter = 1
                        while os.path.exists(frame_path):
                            frame_filename = f"frame_{minutes:02d}{seconds:02d}_{counter}.jpg"
                            frame_path = os.path.join(output_dir, frame_filename)
                            counter += 1
                        
                        cv2.imwrite(frame_path, cropped_frame)
                        
                        frame_data.append({
                            'path': frame_path,
                            'timestamp_seconds': timestamp_sec,
                            'timestamp_str': f"{minutes}:{seconds:02d}",
                            'minutes': minutes,
                            'seconds': seconds
                        })
                        saved_count += 1
                        print(f"Saved frame at {minutes}:{seconds:02d} -> {frame_filename}")
                
                prev_hist = hist
                
            frame_count += 1
            
        cap.release()
        print(f"Extracted {len(frame_data)} frames")
        self._frame_paths = frame_data
        return frame_data

    def parse_transcript_document(self, doc_path: str):
        """Parse transcript and return entries with timestamps"""
        doc = docx.Document(doc_path)
        transcript_data = []
        
        current_speaker = ""
        current_time = ""
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
                
            if paragraph.runs:
                for run in paragraph.runs:
                    if run.bold and text:
                        current_speaker = text.replace('**', '')
                        break
                        
            time_pattern = r'\b(\d{1,2}:\d{2})\b'
            time_match = re.search(time_pattern, text)
            
            if time_match:
                current_time = time_match.group(1)
                text = re.sub(time_pattern, '', text).strip()
                
            if current_speaker and text and not re.match(r'^\d{1,2}:\d{2}$', text):
                transcript_data.append({
                    'timestamp': current_time,
                    'text': text,
                    'time_seconds': self._convert_to_seconds(current_time)
                })
                
        return transcript_data
        
    def _convert_to_seconds(self, time_str: str) -> int:
        """Convert MM:SS or M:SS format to total seconds"""
        if not time_str:
            return 0
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
        except:
            pass
        return 0

    def analyze_transcript_with_comprehensive_prompt(self, transcript_data, custom_prompt: str = "", additional_docs_content: str = ""):
        """
        SINGLE API CALL using comprehensive prompt
        Returns: (inference_data, functionalities_list)
        """
        print("\n" + "="*70)
        print("ANALYZING TRANSCRIPT - COMPREHENSIVE PROMPT")
        print("="*70 + "\n")
        
        combined_transcript = "\n".join([
            f"[{entry['timestamp']}] {entry['text']}"
            for entry in transcript_data
        ])
        
        # Get client_name, stakeholders, systems_text, current_date for the prompt
        client_name = "CLIENT NAME"

        current_date = datetime.now().strftime('%d/%m/%Y')
        
        # BUILD COMPREHENSIVE PROMPT (DO NOT MODIFY - IT WORKS PERFECTLY)
        base_prompt = """
        You are an expert technical writer creating Process Design Documents (PDDs) for AI Agent workflows. Your sole task is to analyze the raw, descriptive text provided below (which is a transcript of someone explaining a procedure) and convert it into a highly detailed, sequential, and numbered list of atomic process steps, suitable for a Process Design Document (PDD).
        **DO NOT** summarize, paraphrase, or omit any information. Every distinct action, decision, and data point mentioned must be converted into a formal step.
        """

        # Add additional docs section if provided
        if additional_docs_content:
            base_prompt += f"""

    **ADDITIONAL SUPPORTING DOCUMENTS PROVIDED:**
    The following supporting documents contain reference information, procedures, or context that should be incorporated into the process steps where relevant:

    {additional_docs_content}

    **IMPORTANT:** Use the information from these additional documents to:
    - Add missing steps that are mentioned in the supporting docs but not in the transcript
    - Clarify ambiguous steps with details from the supporting docs
    - Include specific field names, screen names, or workflow details mentioned in the docs
    - Incorporate best practices or standard procedures outlined in the docs
    - Reference the supporting docs when adding steps (e.g., "As per supporting documentation, the AI Agent...")

    """
                
        if custom_prompt:
            base_prompt += f"""

        **ADDITIONAL CUSTOM INSTRUCTIONS:**
        {custom_prompt}

        Please incorporate these custom instructions while maintaining all other requirements below.
        """
                
        comprehensive_prompt = base_prompt + f"""

        **TRANSCRIPT CONTENT TO ANALYZE:**
        {combined_transcript}

        **CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:**

        1. **USE ONLY TRANSCRIPT CONTENT**: ALL content must be extracted and derived SOLELY from the provided transcript. Do not invent or add information not present in the transcript.
        2. **AI AGENT PERSPECTIVE**: All process steps must be written from AI Agent's first-person perspective (e.g., "The AI Agent opens...", "The AI Agent logs in...", "The AI Agent clicks...")
        3. **DETAILED STEP-BY-STEP PROCESS**: Each functionality must have extremely detailed numbered steps (1., 2., 3., etc.) covering every single action mentioned in the transcript.
        4. **DATA EXTRACTION FLOW**: Complete ALL data extraction from eCW portal before moving to CoverMyMeds portal
        5. **EXCEPTION HANDLING**: Mark any step AI Agent cannot complete as "EXCEPTION" with handling procedure
        6. **WORD CHOICE**: Use "streamline", "fine-tune", "optimize" instead of "automate", "automation", "automated"
        7. **REPEATED SECTIONS**: If same topic/sentence is mentioned twice or more, consolidate only last complete description for that topic. ignore earlier whatever is mentioned.
        8. **FIXED CONTENT**: Use the exact Business Benefits and Risk & Control text provided below
        9. **TIMESTAMP**: Include timestamps from transcript for each functionality section where available (eg., [0:30]The AI Agent logs into the application or portal using the relevant credentials.)


        ADDITIONAL CONTEXT:

        - Try to ADD this step while the new functionality is being implemented(alter the sentence based on the transcript): "The AI Agent logs into the application or portal using the relevant credentials."
        - NEVER use the words "acknowledges" or "reaches out to the team"** in any step description.
        - Instead of "acknowledges" or "double-checks", use "Verifies" or "Validates"** when describing confirmation actions
        - Instead of "stretches out ", the word "Sets" can be used** to describe the action of setting a date range
        - Avoid using steps like "Maximizing/Minimizing the window" the window (exclude these steps)
        - Avoid the usage of the word, "unexpands". For instance, if the AI Agent performs the action of collapsing rows or folders, then instead of "unexpands", The AI Agent collapses the expanded rows or folders.

        **PDD STRUCTURE - FOLLOW EXACTLY:**

        ## Document Revision History
        | Version | Section/Page | Description | Author | Date |
        |---|---|---|---|---|
        | 1.0 | New Document | Draft version for {client_name} - Prior Authorization Process | AI Agent | {current_date} |

        ## Document Sign Off
        | Name | Responsibility | Date |
        |---|---|---|
        | ['business_sme'] or 'Vicki DeLaughter'| Business SME | |
        | ['business_sponsor'] or 'Kelly Martinelli' | Business Sponsor | |
        | ['it_lead'] or 'Vijay Sagar M (Droidal)' | IT Lead | |
        | ['it_developer'] or 'Supraja E (Droidal)' | IT Developer | |

        ## Requirement Summary

        ### Objective
        [Write a 3–4 sentence paragraph strictly based on the transcript using the following template style:
        "This document outlines how the AI Agent streamlines the <process name> by <key activities>."
        Describe what the AI Agent does end-to-end, using formal business language.]

        ### Overview and Current State
        [Write a 4–5 sentence paragraph strictly based on the transcript using the following template style:
        "Currently, the <process name> is performed manually. This requires the team to..."
        Describe the current manual workflow, systems used, effort involved, risks, delays, and inefficiencies.]

        ### Future State (RPA)
        [Write a 4–5 sentence paragraph strictly based on the transcript using the following template style:
        "The AI Agent will handle the entire <process name> end-to-end..."
        Describe how the AI Agent streamlines, fine-tunes, and optimizes the process, including validations, uploads, documentation, and exception handling.]

        | **Systems Impacted** | Applications/Systems or portals involved as mentioned in transcript |
        | **Business Benefits** | • Elimination of manual errors.
                                  • High accuracy of the process.
                                  • Swift execution and efficient handling of volumes.
                                  • Substantial reduction of operational costs and time by eliminating manual efforts. |
        | **Risk & Control** | The AI Agent credentials are stored in an encrypted secret vault within the automation platform. Access to these credentials is restricted. |
        | **Volumes & Frequency** | Needs Confirmation |
        | **Production Schedule** | Needs Confirmation |

        ## Process Map
        ```mermaid
        [Generate HIGH-LEVEL flowchart based on process described in transcript. Focus on main steps only:
        1. Start Process
        2. Access eCW System
        3. Extract Patient & Medication Data
        4. Access CoverMyMeds Portal
        5. Submit Authorization Request
        6. Update eCW Records
        7. Send Summary Report
        8. End Process
        Include basic exception paths]
        ```

        ## Process Steps:

        ### Functionality #1: Accessing eCW and Extracting Patient Data
        **System/Application: eCW**

        [GENERATE EXTREMELY DETAILED NUMBERED STEPS from transcript And Additional docs for eCW data extraction:
        [0:30]1. The AI Agent opens eCW application
        2. The AI Agent enters username and password 
        3. The AI Agent navigates to patient list 
        4. The AI Agent selects patient with Rx Auth
        5. The AI Agent extracts patient details (Last Name, DOB, Key) 
        6. The AI Agent navigates to Telephone Encounters
        7. The AI Agent accesses ePrescription Logs 
        8. The AI Agent extracts provider details and diagnosis codes
        Continue with ALL steps mentioned in transcript...]

        ### Functionality #2: Submitting Prior Authorization in CoverMyMeds
        **System/Application: CoverMyMeds**

        [GENERATE EXTREMELY DETAILED NUMBERED STEPS from transcript And Additional docs for CoverMyMeds submission:
        [4:21]1. The AI Agent opens CoverMyMeds portal 
        2. The AI Agent logs in with credentials
        3. The AI Agent navigates to Enter Key section
        4. The AI Agent enters patient Key, Last Name, and DOB
        5. The AI Agent clicks View Request button
        6. The AI Agent fills patient information form 
        7. The AI Agent enters medication details and quantities
        8. The AI Agent enters diagnosis codes
        9. The AI Agent enters provider NPI and details 
        10. The AI Agent clicks Send to Plan
        Continue with ALL steps mentioned in transcript...]

        ### Functionality #3: Updating Patient Records in eCW
        **System/Application: eCW**

        [GENERATE EXTREMELY DETAILED NUMBERED STEPS from transcript And Additional docs for eCW updates:
        [9:30]1. The AI Agent returns to eCW application
        2. The AI Agent navigates to Patient Hub
        3. The AI Agent clicks New Tel Enc (New Telephone Encounter)
        4. The AI Agent enters Reason for encounter
        5. The AI Agent adds Comments with Key and status
        6. The AI Agent clicks Save to update records
        Include exception handling for denied requests]

        ### Functionality #4: Sending Summary Report via Outlook
        **System/Application: Microsoft Outlook**

        [GENERATE EXTREMELY DETAILED NUMBERED STEPS from transcript for email reporting: (optional based on transcript)
        [11:30]1. The AI Agent opens Microsoft Outlook 
        2. The AI Agent composes new email
        3. The AI Agent attaches summary report
        4. The AI Agent sends email to business team 
        Include email template if provided in transcript]

        """

        # Retry with exponential backoff
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = self.model.generate_content(
                    comprehensive_prompt,
                    request_options={"timeout": 1200}  # Set timeout to 20 minutes
                )
                full_response = response.text.strip()
                
                print("✅ API Response received - parsing sections...")

                mermaid_content = self._extract_process_map(full_response)
                if mermaid_content:
                    mmd_path = self._save_process_map_to_mmd(mermaid_content, "workflow")
                    print(f"📊 Process Map ready at: {mmd_path}")
                
                # PARSE SECTION A (Document Metadata)
                inference_data = self._parse_section_a(full_response)
                
                # PARSE SECTION B (Functionalities)
                functionalities = self._parse_section_b(full_response)
                
                print(f"✅ Parsed {len(functionalities)} functionalities")
                
                return inference_data, functionalities
                
            except google.api_core.exceptions.DeadlineExceeded as e:
                wait = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff
                print(f"❌ Deadline Exceeded on attempt {attempt + 1}/{max_attempts}, retrying in {wait:.1f}s...")
                if attempt == max_attempts - 1:
                    print(f"❌ Max retries reached. Failed to process transcript.")
                    import traceback
                    traceback.print_exc()
                    return {}, []
                time.sleep(wait)
            except Exception as e:
                print(f"❌ Other error in comprehensive analysis: {str(e)}")
                import traceback
                traceback.print_exc()
                return {}, []
            
    def _parse_section_a(self, response_text: str) -> dict:
        inference_data = {}

        def extract_section(header):
            pattern = rf'### {re.escape(header)}\n(.*?)(?=\n### |\n\| \*\*|\n## |\Z)'
            match = re.search(pattern, response_text, re.DOTALL)
            return match.group(1).strip() if match else ""

        # New markdown-based extraction
        inference_data['objective'] = extract_section("Objective")
        inference_data['overview_current_state'] = extract_section("Overview and Current State")
        inference_data['future_state'] = extract_section("Future State (RPA)")

        # Systems Impacted
        systems_match = re.search(r'\|\s*\*\*Systems Impacted\*\*\s*\|\s*(.+?)\s*\|', response_text, re.DOTALL)
        systems_raw = systems_match.group(1).strip() if systems_match else ""
        inference_data['systems_impacted'] = "\n".join(
            [f"• {s.strip()}" for s in re.split(r',|\n', systems_raw) if s.strip()]
        )

        # Business Benefits — native bullets, no <br>
        inference_data['business_benefits'] = "\n".join([
            "• Elimination of manual errors.",
            "• High accuracy of the process.",
            "• Swift execution and efficient handling of volumes.",
            "• Substantial reduction of operational costs and time by eliminating manual efforts."
        ])

        # Risk & Control
        inference_data['risk_control'] = (
            "The AI Agent credentials are stored in an encrypted secret vault within the automation platform. "
            "Access to these credentials is restricted."
        )

        # Volumes & Frequency
        volumes_match = re.search(r'\|\s*\*\*Volumes & Frequency\*\*\s*\|\s*(.+?)\s*\|', response_text, re.DOTALL)
        inference_data['volumes_frequency'] = volumes_match.group(1).strip() if volumes_match else "Needs Confirmation"

        # Production Schedule
        schedule_match = re.search(r'\|\s*\*\*Production Schedule\*\*\s*\|\s*(.+?)\s*\|', response_text, re.DOTALL)
        inference_data['production_schedule'] = schedule_match.group(1).strip() if schedule_match else "Needs Confirmation"

        # Stakeholders
        stakeholders_lines = []
        signoff_pattern = r'## Document Sign Off.*?\n(.*?)(?=##|\Z)'
        signoff_match = re.search(signoff_pattern, response_text, re.DOTALL)

        if signoff_match:
            signoff_text = signoff_match.group(1)
            stakeholder_pattern = r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'
            for match in re.finditer(stakeholder_pattern, signoff_text):
                name = match.group(1).strip()
                responsibility = match.group(2).strip()
                if name not in ("Name", "") and responsibility not in ("Responsibility", ""):
                    stakeholders_lines.append(f"{responsibility}: {name}")

        inference_data['stakeholders'] = "\n".join(stakeholders_lines) if stakeholders_lines else "Input needed"

        # Process name
        process_name_match = re.search(r'Draft version for (.+?) -', response_text)
        inference_data['process_name'] = process_name_match.group(1).strip() if process_name_match else "Process Name"

        print("✅ Document metadata parsed successfully")
        return inference_data


    def _parse_section_b(self, response_text):
        """
        Parse functionalities from Gemini response - EXTRACT ALL TIMESTAMPS
        Match multiple frames per functionality based on step timestamps
        CRITICAL FIX: PRESERVE timestamps in action text for proper image insertion
        """
        functionalities = []
        
        # Find all functionality blocks (### Functionality #N: Title)
        func_pattern = r'### Functionality #(\d+): (.+?)\n\*\*System/Application:\s*(.+?)\*\*\s*\n(.*?)(?=### Functionality #|\Z)'
        func_matches = re.findall(func_pattern, response_text, re.DOTALL)
        
        if not func_matches:
            print("⚠️ No functionality blocks found in response")
            print("Response preview:", response_text[:500])
            return []
        
        for func_num_str, func_title, system, steps_block in func_matches:
            func_num = int(func_num_str)
            
            # TRY PATTERN 1: Steps WITH timestamps [MM:SS]N. Text
            step_pattern_with_timestamp = r'\[(\d{1,2}:\d{2})\]\s*(\d+)\.\s*(.+?)(?=(?:\n\[|\n\d+\.|\Z))'
            step_matches = re.findall(step_pattern_with_timestamp, steps_block, re.DOTALL)
            
            # TRY PATTERN 2: Steps WITHOUT timestamps - just N. Text
            if not step_matches:
                step_pattern_without_timestamp = r'(?:^|\n)(\d+)\.\s*(.+?)(?=(?:\n\d+\.|\Z))'
                step_matches_no_ts = re.findall(step_pattern_without_timestamp, steps_block, re.DOTALL | re.MULTILINE)
                
                # Convert to same format (timestamp, step_num, text) - use "0:00" as placeholder
                step_matches = [("0:00", step_num, text) for step_num, text in step_matches_no_ts]
            
            if not step_matches:
                print(f"⚠️ No steps found for Functionality {func_num}")
                print(f"   Steps block preview: {steps_block[:200]}")
                continue
            
            # Get FIRST step's timestamp as representative timestamp
            first_timestamp = step_matches[0][0] if step_matches else '0:00'
            
            # NEW: Collect ALL timestamps from all steps in this functionality
            all_timestamps = []
            for timestamp, step_num, action_text in step_matches:
                if timestamp != '0:00':  # Skip placeholder timestamps
                    all_timestamps.append(timestamp)
            
            # CRITICAL FIX: Build action list WITH timestamps preserved
            action_list = []
            for timestamp, step_num, action_text in step_matches:
                # Clean action text - handle multi-line actions
                action_clean = action_text.strip()
                # Remove [[Image...]] tags for action list
                action_clean = re.sub(r'\[\[Image of .+?\]\]', '', action_clean).strip()
                # Remove extra whitespace and newlines within action
                action_clean = re.sub(r'\s+', ' ', action_clean)
                
                if action_clean:
                    # CRITICAL: Keep timestamp in the action text if it exists
                    if timestamp != '0:00':
                        action_with_timestamp = f"[{timestamp}]{action_clean}"
                        action_list.append(action_with_timestamp)
                    else:
                        action_list.append(action_clean)
            
            # Build actions_combined WITH timestamps
            actions_combined = '\n'.join(['• ' + a for a in action_list])
            
            functionality = {
                'step_number': func_num,
                'timestamp': first_timestamp,  # First step's timestamp (for backward compatibility)
                'timestamp_seconds': self._convert_to_seconds(first_timestamp),
                'all_timestamps': all_timestamps,  # NEW: List of all timestamps
                'system': self.clean_text_formatting(system),
                'step_title': self.clean_text_formatting(func_title),
                'process_step': self.clean_text_formatting(func_title),
                'step_description': self.clean_text_formatting(func_title),
                'actions': actions_combined,
                'action_list': action_list,  # Contains timestamps
                'frame_path': '',  # Will be updated to list of paths
                'frame_paths': [],  # NEW: List of matched frame paths
                'frame_number': func_num
            }
            
            functionalities.append(functionality)
            print(f"  ✅ Parsed Functionality {func_num}: {func_title}")
            print(f"     Timestamps found: {all_timestamps}")
            print(f"     Actions: {len(action_list)}")
            print(f"     Sample action: {action_list[0][:80] if action_list else 'None'}...")
        
        return functionalities
    
    
    def _extract_process_map(self, response_text: str) -> str:
        """
        Extract mermaid diagram from Gemini API response
        Returns the mermaid code content
        """
        # Pattern to match ## Process Map section with mermaid code block
        pattern = r'## Process Map\s*```mermaid\s*(.*?)```'
        
        match = re.search(pattern, response_text, re.DOTALL)
        
        if match:
            mermaid_content = match.group(1).strip()
            print(f"✅ Process Map extracted ({len(mermaid_content)} chars)")
            return mermaid_content
        else:
            print("⚠️ No Process Map found in response")
            return ""


    def _save_process_map_to_mmd(self, mermaid_content: str, output_dir: str = "workflow") -> str:
        """
        Save mermaid diagram to .mmd file
        Returns the path to the saved .mmd file
        """
        if not mermaid_content:
            print("⚠️ No mermaid content to save")
            return ""
        
        # Save to .mmd file
        mmd_file_path = os.path.join(output_dir, "workflow_diagram.mmd")
        
        try:
            with open(mmd_file_path, 'w', encoding='utf-8') as f:
                f.write(mermaid_content)
            
            print(f"✅ Process Map saved to: {mmd_file_path}")
            return mmd_file_path
        
        except Exception as e:
            print(f"❌ Error saving Process Map: {e}")
            import traceback
            traceback.print_exc()
            return ""


    def find_nearest_frame_for_timestamp(self, target_timestamp: str, frame_data: list, tolerance_seconds: int = 5):
        """
        Find nearest frame for a given timestamp with tolerance
        Now uses flexible matching: exact match OR closest frame within ±tolerance_seconds
        Returns frame data or None if no match found
        """
        target_seconds = self._convert_to_seconds(target_timestamp)
        
        # DEBUG: Print what we're searching for
        print(f"   🔍 Searching for {target_timestamp} ({target_seconds}s)")
        
        # Try exact match first
        for frame in frame_data:
            if abs(frame['timestamp_seconds'] - target_seconds) < 0.5:  # Within 0.5 seconds = exact
                print(f"   ✓ EXACT MATCH: {target_timestamp} → {frame['timestamp_str']} ({frame['timestamp_seconds']}s)")
                return frame
        
        # Find the closest frame within tolerance
        closest_frame = None
        min_diff = float('inf')
        
        for frame in frame_data:
            diff = abs(frame['timestamp_seconds'] - target_seconds)
            
            if diff <= tolerance_seconds and diff < min_diff:
                min_diff = diff
                closest_frame = frame
        
        if closest_frame:
            offset = closest_frame['timestamp_seconds'] - target_seconds
            print(f"   ✓ CLOSEST MATCH: {target_timestamp} ({target_seconds}s) → {closest_frame['timestamp_str']} ({closest_frame['timestamp_seconds']}s) [{offset:+.1f}s]")
            return closest_frame
        
        # DEBUG: Show nearby frames for troubleshooting
        nearby = [f for f in frame_data if abs(f['timestamp_seconds'] - target_seconds) <= 30]
        if nearby:
            print(f"   ℹ️  Nearby frames (within 10s):")
            for f in nearby[:3]:
                diff = f['timestamp_seconds'] - target_seconds
                print(f"      - {f['timestamp_str']} ({f['timestamp_seconds']}s) [{diff:+.1f}s]")
        
        print(f"   ✗ No frame found for {target_timestamp} ({target_seconds}s) within ±{tolerance_seconds}s")
        return None

    def match_frames_to_functionalities(self, functionalities, frame_data):
        """
        Match frames to functionalities with PROGRESSIVE TOLERANCE (±1, ±2, ±3...±15 seconds)
        Each timestamp gets ONE frame - the closest match within tolerance
        """
        print("\n" + "="*70)
        print("MATCHING FRAMES WITH PROGRESSIVE TOLERANCE (±1 to ±15s)")
        print("="*70 + "\n")
        
        # DEBUG: Show first 5 frames
        print("📊 DEBUG - First 5 frames available:")
        for i, frame in enumerate(frame_data[:5]):
            print(f"   Frame {i+1}: timestamp_str='{frame.get('timestamp_str')}', "
                f"timestamp_seconds={frame.get('timestamp_seconds')}, "
                f"path={os.path.basename(frame.get('path', 'NO_PATH'))}")
        print()
        
        for func in functionalities:
            func_num = func['step_number']
            all_timestamps = func.get('all_timestamps', [])
            
            if not all_timestamps:
                # Fallback to single representative timestamp
                rep_timestamp = func.get('timestamp', '0:00')
                all_timestamps = [rep_timestamp]
            
            print(f"Functionality {func_num}: Processing {len(all_timestamps)} timestamp(s)")
            
            matched_frames = []
            used_frame_paths = set()  # Track used frames to avoid duplicates
            
            # Process each timestamp with progressive tolerance
            for timestamp in all_timestamps:
                target_seconds = self._convert_to_seconds(timestamp)
                
                print(f"  🔍 Searching for [{timestamp}] ({target_seconds}s)")
                
                best_match = None
                
                # Progressive tolerance: try ±1, ±2, ±3...±15
                for tolerance in range(1, 16):  # 1 to 15 seconds
                    # Find closest frame within current tolerance
                    candidates = []
                    
                    for frame in frame_data:
                        frame_seconds = frame['timestamp_seconds']
                        diff = abs(frame_seconds - target_seconds)
                        
                        # Check if within current tolerance AND not already used
                        if diff <= tolerance and frame['path'] not in used_frame_paths:
                            candidates.append({
                                'frame': frame,
                                'diff': diff
                            })
                    
                    # If we found candidates, pick the closest one
                    if candidates:
                        # Sort by difference (closest first)
                        candidates.sort(key=lambda x: x['diff'])
                        best_match = candidates[0]['frame']
                        
                        offset = best_match['timestamp_seconds'] - target_seconds
                        print(f"     ✅ MATCH at tolerance ±{tolerance}s: [{timestamp}] → [{best_match['timestamp_str']}] ({best_match['timestamp_seconds']:.1f}s) [offset: {offset:+.1f}s]")
                        break
                
                # Add the matched frame (if found)
                if best_match:
                    matched_frames.append({
                        'path': best_match['path'],
                        'timestamp': best_match['timestamp_str'],
                        'timestamp_seconds': best_match['timestamp_seconds']
                    })
                    used_frame_paths.add(best_match['path'])  # Mark as used
                else:
                    print(f"     ❌ NO MATCH within ±15s for [{timestamp}]")
            
            # Update functionality with matched frames
            func['frame_paths'] = matched_frames
            
            # For backward compatibility, keep first frame as 'frame_path'
            if matched_frames:
                func['frame_path'] = matched_frames[0]['path']
                func['frame_timestamp'] = matched_frames[0]['timestamp']
            else:
                func['frame_path'] = ''
                func['frame_timestamp'] = '0:00'
            
            print(f"  ✅ Functionality {func_num}: Matched {len(matched_frames)} UNIQUE frame(s)")
            for idx, frame in enumerate(matched_frames):
                print(f"     {idx+1}. [{frame['timestamp']}] → {os.path.basename(frame['path'])}")
            print()
        
        return functionalities

    def _set_cell_background(self, cell, color_hex: str, white_text=False):
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        for child in tcPr.findall(qn('w:shd')):
            tcPr.remove(child)
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), color_hex)
        tcPr.append(shd)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.name = 'Times New Roman'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                if white_text:
                    run.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    run.font.color.rgb = RGBColor(0, 0, 0)
    def _set_table_borders(self, table, color='000000', first_row_inner_color='FFFFFF'):
        tbl = table._tbl
        tblPr = tbl.tblPr
       
        existing_borders = tblPr.find(qn('w:tblBorders'))
        if existing_borders is not None:
            tblPr.remove(existing_borders)
       
        tblBorders = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), color)
            tblBorders.append(border)
        tblPr.append(tblBorders)
       
        first_row = table.rows[0]
        for cell in first_row.cells:
            tcPr = cell._element.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
           
            right_border = OxmlElement('w:right')
            right_border.set(qn('w:val'), 'single')
            right_border.set(qn('w:sz'), '4')
            right_border.set(qn('w:space'), '0')
            right_border.set(qn('w:color'), first_row_inner_color)
            tcBorders.append(right_border)
           
            tcPr.append(tcBorders)
    def _apply_table_theme(self, table):
        dark_blue = "4472C4"
        light_blue_1 = "D9E2F3"
        light_blue_2 = "FFFFFF"
        if not table.rows:
            return
        for cell in table.rows[0].cells:
            self._set_cell_background(cell, dark_blue, white_text=True)
        for i, row in enumerate(table.rows[1:], start=1):
            color = light_blue_1 if i % 2 == 0 else light_blue_2
            for cell in row.cells:
                self._set_cell_background(cell, color, white_text=False)
                
    
    def add_workflow_diagram_png(self, doc, workflow_dir="workflow"):
        """
        Add the saved workflow PNG diagram to the document.
        This replaces the text-based workflow with the actual flowchart image.
        """
        png_file_path = os.path.join(workflow_dir, "workflow_diagram.png")
        
        # Check if PNG exists
        if not os.path.exists(png_file_path):
            print(f"⚠️ Workflow PNG not found at: {png_file_path}")
            # Fallback to text-based workflow
            p = doc.add_paragraph("Workflow Diagram: [PNG not available]")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            return
        
        try:
            # Add the PNG image centered in the document
            doc.add_paragraph()  # Add spacing before
            
            pic_paragraph = doc.add_paragraph()
            pic_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            pic_run = pic_paragraph.add_run()
            
            # Get image dimensions to calculate appropriate width
            from PIL import Image
            with Image.open(png_file_path) as img:
                width, height = img.size
                aspect_ratio = height / width
                
                # Set width based on page size (6.5" usable width in portrait)
                # Use 6" to leave some margin
                target_width = Inches(6.0)
                target_height = target_width * aspect_ratio
                
                # If height is too large, scale down
                max_height = Inches(8.0)  # Maximum height to fit on page
                if target_height > max_height:
                    target_height = max_height
                    target_width = target_height / aspect_ratio
            
            # Add the picture with calculated dimensions
            pic_run.add_picture(png_file_path, width=target_width)
            
            doc.add_paragraph()  # Add spacing after
            
            print(f"✅ Workflow PNG added to document: {png_file_path}")
            # Convert Inches object to float for printing
            width_in_inches = target_width / Inches(1)
            height_in_inches = target_height / Inches(1)
            print(f"   Dimensions: {width_in_inches:.2f}\" x {height_in_inches:.2f}\"")
            
        except Exception as e:
            print(f"❌ Error adding workflow PNG: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to text message
            p = doc.add_paragraph(f"Workflow Diagram: [Error loading PNG - {str(e)}]")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER



    def add_header_logo_and_title(self, doc, client_name, process_name):
        logo_path = resource_path("styles\Icon\Droidal_png.png")
        for section in doc.sections:
            header = section.header
            header_paragraph = header.paragraphs[0]
            run = header_paragraph.add_run()
            try:
                run.add_picture(logo_path, width=Inches(1.3))
            except Exception as e:
                header_paragraph.add_run("[Logo not found]")
            header_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for _ in range(9):
            doc.add_paragraph()
        title1 = doc.add_paragraph()
        title1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run1 = title1.add_run("AI Agent")
        run1.font.name = 'Times New Roman'
        run1._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        run1.font.size = Pt(30)
        run1.bold = True
        title2 = doc.add_paragraph()
        title2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run2 = title2.add_run("Process Design Document")
        run2.font.name = 'Times New Roman'
        run2._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        run2.font.size = Pt(26)
        run2.bold = True
        doc.add_paragraph()
        title3 = doc.add_paragraph()
        title3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run3 = title3.add_run(f"{client_name} – {process_name}")
        run3.font.name = 'Times New Roman'
        run3._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        run3.font.size = Pt(20)
        doc.add_paragraph()
        title4 = doc.add_paragraph()
        title4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run4 = title4.add_run("Version 1.0")
        run4.font.name = 'Times New Roman'
        run4._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        run4.font.size = Pt(14)
        try:
            h1 = doc.styles['Heading 1']
            h1.font.name = 'Times New Roman'
            h1._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
            h1.font.size = Pt(14)
            h1.font.bold = True
        except:
            pass
    def _apply_global_styles(self, doc):
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        style.font.size = Pt(12)
        try:
            h1 = doc.styles['Heading 1']
            h1.font.name = 'Times New Roman'
            h1._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
            h1.font.size = Pt(14)
            h1.font.bold = True
        except:
            pass


    def format_requirement_summary_table(self, doc, req_summary_dict):
        """Create requirement summary table - WORD OPTIMIZED"""
       
        fields = [
            ("Stakeholders", "stakeholders"),
            ("Objective", "objective"),
            ("Overview and Current State", "overview_current_state"),
            ("Future State", "future_state"),
            ("Systems Impacted", "systems_impacted"),
            ("Business Benefits", "business_benefits"),
            ("Risk & Control", "risk_control"),
            ("Volumes & Frequency", "volumes_frequency"),
            ("Production Schedule", "production_schedule")
        ]
        table = doc.add_table(rows=0, cols=2)
        table.style = 'Table Grid'
        table.autofit = False
       
        # CRITICAL: Remove indentation
        self._remove_table_indentation(table)
        # Column widths for 6.5" total
        table.columns[0].width = Inches(1.4) # Labels
        table.columns[1].width = Inches(5.1) # Content
        row_idx = 0
        for field_name, key in fields:
            value = req_summary_dict.get(key, "")
           
            if not isinstance(value, str):
                if isinstance(value, (list, tuple)):
                    value = "\n".join([str(item) for item in value if item])
                elif isinstance(value, dict):
                    value = "\n".join([f"{k}: {v}" for k, v in value.items() if v])
                else:
                    value = str(value)
            value = value.strip() if value else ""
            row_cells = table.add_row().cells
            # Label cell
            row_cells[0].text = field_name
            self._set_cell_background(row_cells[0], "4472C4", white_text=True)
            row_cells[0].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in row_cells[0].paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                    run.font.size = Pt(12)
                    run.font.bold = True
            # Content cell
            p = row_cells[1].paragraphs[0]
            p.text = ""
            p.add_run("\n")
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            bullet_fields = ["future_state", "systems_impacted", "business_benefits"]
            items = [line.strip("-• ") for line in value.split("\n") if line.strip()]
           
            if key in bullet_fields and value:
                for item in items:
                    p = row_cells[1].add_paragraph("• " + item)
                    p.paragraph_format.left_indent = Inches(0.2)
                    for run in p.runs:
                        run.font.name = 'Times New Roman'
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                        run.font.size = Pt(12)
            elif key == "stakeholders" and value:
                for item in items:
                    p = row_cells[1].add_paragraph(item)
                    for run in p.runs:
                        run.font.name = 'Times New Roman'
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                        run.font.size = Pt(12)
            else:
                row_cells[1].add_paragraph(value)
                p_after = row_cells[1].add_paragraph("\n")
                for p in row_cells[1].paragraphs:
                    for run in p.runs:
                        run.font.name = 'Times New Roman'
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                        run.font.size = Pt(12)
            # Alternate colors
            if row_idx == 0:
                color = "4472C4"
            else:
                color = "D9E2F3" if row_idx % 2 == 0 else "FFFFFF"
            self._set_cell_background(row_cells[1], color, white_text=False)
            row_idx += 1
        self._set_table_borders(table, 'FFFFFF')
        return table
    def set_document_margins(self, doc):
        """Set standard Word margins"""
        for section in doc.sections:
            # Standard Word margins - 1 inch all around
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)
           
            # Set page size explicitly
            section.page_width = Inches(8.5) # Letter width
            section.page_height = Inches(11) # Letter height
           
    def group_steps_by_functionality(self, pdd_analyses: List[Dict]) -> List[Dict]:
        grouped = []
        current_group = None
       
        for analysis in pdd_analyses:
            process_step = analysis.get('process_step', 'Unknown Process')
           
            if current_group is None or current_group['process_step'] != process_step:
                if current_group is not None:
                    grouped.append(current_group)
               
                current_group = {
                    'process_step': process_step,
                    'system': analysis.get('system', ''),
                    'functionality_title': process_step,
                    'steps': []
                }
           
            current_group['steps'].append(analysis)
       
        if current_group is not None:
            grouped.append(current_group)
       
        return grouped
   


    def create_pdd_document(self, video_title: str, pdd_analyses: list, 
                           inference_data: dict, output_dir: str = "analysis_output", 
                           worker_thread=None) -> str:
        """
        Modified to fix MS Word alignment issues
        """
        
        if worker_thread is not None:
            print("📋 Requesting main thread to show review dialog...")
            worker_thread.show_review_dialog.emit(self, pdd_analyses, self._last_video_path, output_dir)
            
            print("⏳ Waiting for user to complete review...")
            final_steps = worker_thread.wait_for_review()
            
            if final_steps is None or len(final_steps) == 0:
                print("❌ User cancelled step review.")
                return ""
            
            pdd_analyses = final_steps
            print(f"✅ Proceeding with {len(final_steps)} reviewed steps")
    
        doc = Document()
        self.set_document_margins(doc)
        self._apply_global_styles(doc)
        
        process_name = inference_data.get("process_name", "Process Name")
        client_name = "CLIENT NAME"
        
        self.add_header_logo_and_title(doc, client_name, process_name)
        for _ in range(8):
            doc.add_paragraph()
        doc.add_page_break()
        

        heading = doc.add_heading('1. Document Revision History', level=1)
        for run in heading.runs:
            run.font.name = 'Times New Roman'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
            run.font.size = Pt(16)
        doc.add_paragraph()
        doc.add_paragraph("This section records the history of significant changes to this document. Only the most significant changes are described here. The document version number denotes the document information changes. The version number will be increased by 1.0 if significant changes are made. The version number will be increased by 0.1 if minor changes are made to improve its readability without affecting its meaning or intent.")
        doc.add_paragraph()
        
        rev_table = doc.add_table(rows=1, cols=5)
        rev_table.style = 'Table Grid'
        rev_table.autofit = False
        self._remove_table_indentation(rev_table)
        rev_table.columns[0].width = Inches(0.65)
        rev_table.columns[1].width = Inches(1.0)
        rev_table.columns[2].width = Inches(2.5)
        rev_table.columns[3].width = Inches(0.9)
        rev_table.columns[4].width = Inches(1.45)
        
        hdr_cells = rev_table.rows[0].cells
        headers = ['Version', 'Section/Page', 'Description', 'Author', 'Date']
        for i, h in enumerate(headers):
            hdr_cells[i].text = h
            for paragraph in hdr_cells[i].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.bold = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(12)
        
        row = rev_table.add_row().cells
        row[0].text = '1.0'
        row[1].text = 'New Document'
        row[2].text = f'Draft version for {process_name} Workflow'
        row[3].text = 'Author Name'
        row[4].text = datetime.now().strftime('%d/%m/%Y')
        self._apply_table_theme(rev_table)
        self._set_table_borders(rev_table, '4472C4')
        doc.add_paragraph()
    
        heading = doc.add_heading('2. Document Sign Off', level=1)
        for run in heading.runs:
            run.font.name = 'Times New Roman'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
            run.font.size = Pt(16)
        doc.add_paragraph()
        doc.add_paragraph("The following table contains the people required to sign off and review this document and those who need the document for information only.")
        doc.add_paragraph()
        
        sign_table = doc.add_table(rows=1, cols=3)
        sign_table.style = 'Table Grid'
        sign_table.autofit = False
        self._remove_table_indentation(sign_table)
        sign_table.columns[0].width = Inches(2.16)
        sign_table.columns[1].width = Inches(2.16)
        sign_table.columns[2].width = Inches(2.18)
        
        hdr_cells = sign_table.rows[0].cells
        headers = ['Name', 'Responsibility', 'Date']
        for i, h in enumerate(headers):
            hdr_cells[i].text = h
            for paragraph in hdr_cells[i].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.bold = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(12)
        
        for _ in range(2):
            sign_table.add_row()
        self._apply_table_theme(sign_table)
        self._set_table_borders(sign_table, '4472C4')
        doc.add_paragraph()
        
        heading = doc.add_heading('3. Requirement Summary', level=1)
        for run in heading.runs:
            run.font.name = 'Times New Roman'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
            run.font.size = Pt(16)
        doc.add_paragraph()
        self.format_requirement_summary_table(doc, inference_data)
        
        for _ in range(12):
            doc.add_paragraph()
        
        heading = doc.add_heading('4. Process Workflow', level=1)
        for run in heading.runs:
            run.font.name = 'Times New Roman'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
            run.font.size = Pt(16)
        
        doc.add_paragraph()  # Add spacing
        
        # Add the saved PNG workflow diagram
        workflow_dir = os.path.abspath("workflow")
        self.add_workflow_diagram_png(doc, workflow_dir)
        
        doc.add_paragraph()
        
        heading = doc.add_heading('5. Process Steps:', level=1)
        for run in heading.runs:
            run.font.name = 'Times New Roman'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
            run.font.size = Pt(16)
        doc.add_paragraph()
        
        # ============================================================
        # IMPROVED PROCESS STEPS TABLE - MS WORD COMPATIBLE
        # ============================================================


        grouped_functionalities = self.group_steps_by_functionality(pdd_analyses)

        print("\n" + "="*70)
        print("DEBUG: ANALYZING FUNCTIONALITIES DATA STRUCTURE")
        print("="*70)
        for idx, func in enumerate(grouped_functionalities):
            print(f"\nFunctionality {idx+1}:")
            print(f"  Title: {func.get('functionality_title', 'N/A')}")
            print(f"  Number of steps: {len(func.get('steps', []))}")
            for step_idx, step in enumerate(func.get('steps', [])):
                print(f"  Step {step_idx+1}:")
                print(f"    - frame_path: {step.get('frame_path', 'N/A')}")
                print(f"    - frame_paths type: {type(step.get('frame_paths', []))}")
                print(f"    - frame_paths: {step.get('frame_paths', [])}")
                print(f"    - actions preview: {step.get('actions', '')[:100]}...")
        print("="*70 + "\n")

        proc_table = doc.add_table(rows=1, cols=3)
        proc_table.style = 'Table Grid'
        proc_table.autofit = False
        proc_table.allow_autofit = False

        # CRITICAL: Remove all indentation
        self._remove_table_indentation(proc_table)
        self._set_table_alignment_left(proc_table)

        # Column widths
        proc_table.columns[0].width = Inches(0.35)  # #
        proc_table.columns[1].width = Inches(1.15)  # Steps
        proc_table.columns[2].width = Inches(5.0)   # AI Agent Flow

        # Header row
        hdr_cells = proc_table.rows[0].cells
        hdr_cells[0].text = '#'
        hdr_cells[1].text = 'Steps'
        hdr_cells[2].text = 'AI Agent Flow'

        for c in hdr_cells:
            for p in c.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.bold = True
                    run.font.name = 'Times New Roman'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                    run.font.size = Pt(12)

        step_number = 1
        functionality_number = 1

        for func_group in grouped_functionalities:
            # COMBINED FUNCTIONALITY + SYSTEM HEADER ROW
            func_row = proc_table.add_row()
            func_cells = func_row.cells
            func_cells[0].merge(func_cells[1]).merge(func_cells[2])

            func_title = func_group.get("functionality_title", f"Functionality {functionality_number}")
            system_name = func_group.get("system", "Business Application")

            combined_title = f'Functionality #{functionality_number}: {func_title}\nSystem/Application: {system_name}'
            func_cells[0].text = combined_title

            para = func_cells[0].paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT

            for run in para.runs:
                run.bold = True
                run.font.name = 'Times New Roman'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                run.font.size = Pt(12)

            # Single background color
            self._set_cell_background(func_cells[0], "B4C7E7", white_text=False)
            func_cells[0]._element.get_or_add_tcPr()
            
            # STEP CONTENT ROW
            step_row = proc_table.add_row()
            
            # Column 1: Step Number
            cell_num = step_row.cells[0]
            cell_num.text = str(step_number)
            cell_num.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
            for p in cell_num.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                    run.font.size = Pt(12)
            
            # Column 2: Step Description
            cell_step = step_row.cells[1]
            step_desc = func_group['steps'][0].get('step_description', func_group.get('functionality_title', ''))
            step_desc = step_desc.replace('The AI Agent', '').replace('AI Agent', '').strip()
            cell_step.text = f"{step_desc}"
            cell_step.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            # ADD THIS: Force vertical center at XML level
            tc = cell_step._tc
            tcPr = tc.get_or_add_tcPr()
            vAlign = OxmlElement('w:vAlign')
            vAlign.set(qn('w:val'), 'center')
            tcPr.append(vAlign)

            for p in cell_step.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                    run.font.size = Pt(12)
                    run.font.bold = True
            
            # Column 3: AI Agent Flow with Images
            flow_cell = step_row.cells[2]
            flow_cell.text = ''

            print(f"\n{'='*70}")
            print(f"Processing Functionality #{functionality_number}: {func_title}")
            print(f"{'='*70}")

            # Process actions and images together
            for step_idx, step in enumerate(func_group['steps']):
                actions_text = step.get('actions', '')
                
                # Get frame_paths - handle different formats
                frame_paths = step.get('frame_paths', [])
                if not frame_paths and step.get('frame_path'):
                    # Fallback to single frame_path
                    frame_paths = [{'path': step['frame_path'], 'timestamp': step.get('timestamp', '0:00')}]
                
                print(f"\n  Step {step_idx+1}:")
                print(f"    Frame paths: {len(frame_paths)} unique images")
                
                if actions_text:
                    actions_text = actions_text.replace('**', '"')
                    lines = actions_text.split('\n')
                    
                    # Build timestamp to image mapping
                    timestamp_to_images = {}
                    
                    for frame in frame_paths:
                        if isinstance(frame, dict):
                            frame_ts = frame.get('timestamp', '0:00')
                            frame_path = frame.get('path', '')
                            frame_seconds = frame.get('timestamp_seconds', 0)
                        else:
                            frame_path = frame
                            frame_ts = step.get('timestamp', '0:00')
                            frame_seconds = 0
                        
                        if frame_ts != '0:00' and frame_path and os.path.exists(frame_path):
                            timestamp_to_images[frame_ts] = {
                                'path': frame_path,
                                'seconds': frame_seconds
                            }
                    
                    print(f"    📷 Available: {len(timestamp_to_images)} unique timestamps with images")
                    
                    # Sort all available images by timestamp (chronologically)
                    sorted_images = sorted(timestamp_to_images.items(), key=lambda x: x[1]['seconds'])
                    
                    # Extract action timestamps from text
                    action_timestamps = []
                    for line in lines:
                        timestamp_match = re.search(r'\[(\d{1,2}:\d{2})\]', line)
                        if timestamp_match:
                            ts = timestamp_match.group(1)
                            action_timestamps.append(self._convert_to_seconds(ts))
                    
                    # If we have action points, get first and last timestamps
                    if action_timestamps and sorted_images:
                        first_action_seconds = min(action_timestamps)
                        last_action_seconds = max(action_timestamps)
                        
                        print(f"    📍 Action range: {first_action_seconds}s - {last_action_seconds}s")
                        
                        # Filter images to only those within the action range
                        images_in_range = [
                            (ts, data) for ts, data in sorted_images
                            if first_action_seconds <= data['seconds'] <= last_action_seconds
                        ]
                        
                        print(f"    📷 Images in action range: {len(images_in_range)}")
                        
                        # ==================================================
                        # MODIFIED: Use native Word bullets + Remove timestamps
                        # ==================================================
                        if len(lines) > 1 and images_in_range:
                            images_per_section = len(images_in_range) / len(lines)
                            image_index = 0
                            
                            # First paragraph needs bullet list initialization
                            first_line_added = False
                            
                            for line_idx, line in enumerate(lines):
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # REMOVE TIMESTAMP from line content
                                timestamp_match = re.match(r'[•➢]?\s*\[(\d{1,2}:\d{2})\](.+)', line)
                                
                                if timestamp_match:
                                    line_content = timestamp_match.group(2).strip()
                                else:
                                    line_content = re.sub(r'^[•➢]\s*', '', line).strip()
                                
                                # Remove manual bullet if present
                                line_content = re.sub(r'^[•➢]\s*', '', line_content).strip()
                                
                                if line_content:
                                    p = flow_cell.add_paragraph()
                                    
                                    # Set bullet style based on line type
                                    if line.startswith('➢'):
                                        # Sub-bullet (indented)
                                        p.style = 'List Bullet 2'  # Built-in sub-bullet style
                                    else:
                                        # Main bullet
                                        p.style = 'List Bullet'  # Built-in bullet style
                                    
                                    # Add formatted text (with quote bolding)
                                    self._add_formatted_text_with_quotes(p, line_content)
                                    
                                    # Formatting
                                    p.paragraph_format.space_before = Pt(2)
                                    p.paragraph_format.space_after = Pt(2)
                                    p.paragraph_format.line_spacing = 1.15
                                    
                                    for run in p.runs:
                                        run.font.name = 'Times New Roman'
                                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                                        run.font.size = Pt(12)
                                    
                                    first_line_added = True
                                
                                # Calculate how many images to insert after this line
                                next_image_index = int((line_idx + 1) * images_per_section)
                                
                                # Insert images chronologically between this line and the next
                                while image_index < next_image_index and image_index < len(images_in_range):
                                    ts, img_data = images_in_range[image_index]
                                    img_path = img_data['path']
                                    
                                    pic_p = flow_cell.add_paragraph()
                                    pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    pic_p.paragraph_format.space_before = Pt(6)
                                    pic_p.paragraph_format.space_after = Pt(6)
                                    
                                    pic_run = pic_p.add_run()
                                    pic_run.add_picture(img_path, width=Inches(4.0))
                                    
                                    print(f"    ✅ IMAGE [{ts}] INSERTED after line {line_idx+1}: {os.path.basename(img_path)}")
                                    image_index += 1
                            
                            # Insert any remaining images at the end
                            while image_index < len(images_in_range):
                                ts, img_data = images_in_range[image_index]
                                img_path = img_data['path']
                                
                                pic_p = flow_cell.add_paragraph()
                                pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                pic_p.paragraph_format.space_before = Pt(6)
                                pic_p.paragraph_format.space_after = Pt(6)
                                
                                pic_run = pic_p.add_run()
                                pic_run.add_picture(img_path, width=Inches(4.0))
                                
                                print(f"    ✅ REMAINING IMAGE [{ts}] INSERTED: {os.path.basename(img_path)}")
                                image_index += 1
                        
                    else:
                        # Fallback: No action timestamps found
                        print(f"    ℹ️ No action timestamps found, distributing images evenly")
                        
                        if sorted_images:
                            images_per_line = len(sorted_images) / max(len(lines), 1)
                            image_index = 0
                            
                            for line_idx, line in enumerate(lines):
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # REMOVE TIMESTAMP from line
                                line_content = line.strip()
                                line_content = re.sub(r'\[\d{1,2}:\d{2}\]', '', line_content)  # Remove [MM:SS] anywhere
                                line_content = re.sub(r'^[•➢]\s*', '', line_content).strip()  # Remove leading bullets
                                line_content = line_content.strip()  # Final cleanup
                                
                                
                                if line_content:
                                    p = flow_cell.add_paragraph()
                                    
                                    if line.startswith('➢'):
                                        p.style = 'List Bullet 2'
                                    else:
                                        p.style = 'List Bullet'
                                    
                                    self._add_formatted_text_with_quotes(p, line_content)
                                    
                                    p.paragraph_format.space_before = Pt(2)
                                    p.paragraph_format.space_after = Pt(2)
                                    p.paragraph_format.line_spacing = 1.15
                                    
                                    for run in p.runs:
                                        run.font.name = 'Times New Roman'
                                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                                        run.font.size = Pt(12)
                                
                                # Insert images proportionally
                                next_image_index = int((line_idx + 1) * images_per_line)
                                
                                while image_index < next_image_index and image_index < len(sorted_images):
                                    ts, img_data = sorted_images[image_index]
                                    img_path = img_data['path']
                                    
                                    pic_p = flow_cell.add_paragraph()
                                    pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    pic_p.paragraph_format.space_before = Pt(6)
                                    pic_p.paragraph_format.space_after = Pt(6)
                                    
                                    pic_run = pic_p.add_run()
                                    pic_run.add_picture(img_path, width=Inches(4.0))
                                    
                                    print(f"    ✅ IMAGE [{ts}] INSERTED: {os.path.basename(img_path)}")
                                    image_index += 1
                        
                        # FALLBACK: No images - just add text with native bullets
                        else:
                            print(f"    ℹ️ No images matched - adding text points with native bullets")
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # REMOVE TIMESTAMP and manual bullets
                                line_content = line.strip()
                                line_content = re.sub(r'\[\d{1,2}:\d{2}\]', '', line_content)  # Remove [MM:SS] anywhere
                                line_content = re.sub(r'^[•➢]\s*', '', line_content).strip()  # Remove leading bullets
                                line_content = line_content.strip()  # Final cleanup
                                
                                if line_content:
                                    p = flow_cell.add_paragraph()
                                    
                                    if line.startswith('➢'):
                                        p.style = 'List Bullet 2'
                                    else:
                                        p.style = 'List Bullet'
                                    
                                    self._add_formatted_text_with_quotes(p, line_content)
                                    
                                    p.paragraph_format.space_before = Pt(2)
                                    p.paragraph_format.space_after = Pt(2)
                                    p.paragraph_format.line_spacing = 1.15
                                    
                                    for run in p.runs:
                                        run.font.name = 'Times New Roman'
                                        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                                        run.font.size = Pt(12)
                                                        
            step_number += 1
            functionality_number += 1

        # Apply theme and borders
        self._apply_table_theme(proc_table)
        self._set_table_borders(proc_table, '4472C4')

        # Lock column widths at cell level
        for row in proc_table.rows:
            row.cells[0].width = Inches(0.35)
            row.cells[1].width = Inches(1.15)
            row.cells[2].width = Inches(5.0)
            
            for cell_idx, cell in enumerate(row.cells):
                tc = cell._tc
                tcPr = tc.tcPr
                
                if tcPr is None:
                    tcPr = OxmlElement('w:tcPr')
                    tc.insert(0, tcPr)
                
                tcW = tcPr.find(qn('w:tcW'))
                if tcW is not None:
                    tcPr.remove(tcW)
                
                tcW = OxmlElement('w:tcW')
                if cell_idx == 0:
                    tcW.set(qn('w:w'), '504')
                elif cell_idx == 1:
                    tcW.set(qn('w:w'), '1656')
                else:
                    tcW.set(qn('w:w'), '7200')
                
                tcW.set(qn('w:type'), 'dxa')
                tcPr.append(tcW)
                
                tcMar = OxmlElement('w:tcMar')
                for margin_name in ['top', 'left', 'bottom', 'right']:
                    margin = OxmlElement(f'w:{margin_name}')
                    margin.set(qn('w:w'), '100')
                    margin.set(qn('w:type'), 'dxa')
                    tcMar.append(margin)
                tcPr.append(tcMar)
                
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.name = 'Times New Roman'
                        r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                        r.font.size = Pt(12)

        doc.add_paragraph()
        
        
        # Save document
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_video_title = self.clean_text_formatting(video_title.replace(' ', '_').replace('/', '_'))
        pdd_filename = f"{clean_video_title}.docx"
        pdd_file = os.path.join(output_dir, pdd_filename)
        doc.save(pdd_file)
        print(f"PDD document saved to {pdd_file}")
        return pdd_file



    def _add_formatted_text_with_quotes(self, paragraph, text):

        import re

        # Split by straight-quoted text
        parts = re.split(r'(".*?")', text)

        for part in parts:
            if part.startswith('"') and part.endswith('"'):
                # Remove straight quotes
                inner_text = part[1:-1]

                # Add curly quotes
                curly_text = f"“{inner_text}”"

                run = paragraph.add_run(curly_text)
                run.bold = True
            else:
                run = paragraph.add_run(part)
                run.bold = False



    def _set_table_alignment_left(self, table):
        """Align table to left with no indentation"""
        tbl = table._tbl
        tblPr = tbl.tblPr
        
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            tbl.insert(0, tblPr)
        
        # Remove existing alignment
        existing_jc = tblPr.find(qn('w:jc'))
        if existing_jc is not None:
            tblPr.remove(existing_jc)
        
        # Set alignment to left
        jc = OxmlElement('w:jc')
        jc.set(qn('w:val'), 'left')
        tblPr.append(jc)


    def _remove_table_indentation(self, table):
        """Remove table indentation completely and lock table width"""
        tbl = table._tbl
        tblPr = tbl.tblPr
        
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            tbl.insert(0, tblPr)
        
        # Remove indentation
        tblInd = tblPr.find(qn('w:tblInd'))
        if tblInd is not None:
            tblPr.remove(tblInd)
        
        # Set table width to fixed (prevent auto-resize)
        tblW = tblPr.find(qn('w:tblW'))
        if tblW is not None:
            tblPr.remove(tblW)
        
        tblW = OxmlElement('w:tblW')
        tblW.set(qn('w:w'), '9360')  # 6.5 inches in twips (6.5 * 1440 = 9360)
        tblW.set(qn('w:type'), 'dxa')  # dxa = twips (fixed width)
        tblPr.append(tblW)
        
        # Disable auto-fit
        tblLayout = tblPr.find(qn('w:tblLayout'))
        if tblLayout is not None:
            tblPr.remove(tblLayout)
        
        tblLayout = OxmlElement('w:tblLayout')
        tblLayout.set(qn('w:type'), 'fixed')
        tblPr.append(tblLayout)

    def process_video_and_transcript(self, video_path: str, doc_path: str,
                                    output_dir: str = "analysis_output",
                                    create_pdd: bool = True,
                                    crop_frames: bool = True,
                                    crop_right_percent: float = 0.13,
                                    worker_thread=None,
                                    custom_prompt: str = "",
                                    **kwargs) -> dict:
        """
        REFACTORED WORKFLOW:
        1. Extract frames
        2. Parse transcript
        3. Single API call → get inference_data + functionalities
        4. Match frames to functionalities
        5. Show review dialog
        6. Generate flowchart
        7. Create final document
        """
        self._last_video_path = video_path
        
        print("\n" + "="*70)
        print("REFACTORED WORKFLOW - SINGLE API CALL")
        print("="*70)
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Step 1: Extract frames
        print("Step 1: Extracting frames...")
        frame_data = self.extract_frames_from_video(
            video_path,
            os.path.join(output_dir, "frames"),
            crop_frames=crop_frames,
            crop_right_percent=crop_right_percent
        )
        
        # Step 2: Parse transcript
        print("\nStep 2: Parsing transcript...")
        transcript_data = self.parse_transcript_document(doc_path)
        print(f"Found {len(transcript_data)} transcript entries")
        
        # Step 3: SINGLE API CALL - Get everything
        print("\nStep 3: Comprehensive analysis (SINGLE API CALL)...")
        inference_data, functionalities = self.analyze_transcript_with_comprehensive_prompt(
            transcript_data, custom_prompt
        )
        
        if not functionalities:
            raise RuntimeError("No functionalities extracted from transcript")
        
        # Step 4: Match frames
        print("\nStep 4: Matching frames to functionalities...")
        functionalities = self.match_frames_to_functionalities(functionalities, frame_data)
        
        # Step 5: Show review dialog (if worker thread provided)
        if worker_thread is not None:
            print("\nStep 5: Showing review dialog...")
            worker_thread.show_review_dialog.emit(
                self, functionalities, video_path, output_dir
            )
            
            final_functionalities = worker_thread.wait_for_review()
            
            if final_functionalities is None or len(final_functionalities) == 0:
                print("❌ User cancelled review")
                return {}
            
            functionalities = final_functionalities
            print(f"✅ User approved {len(functionalities)} functionalities")
        
        # Step 6: Create document
        pdd_file = None
        if create_pdd:
            print("\nStep 6: Creating PDD document...")
            video_title = os.path.basename(video_path).split('.')[0].replace('-', ' ').replace('_', ' ')
            pdd_file = self.create_pdd_document(
                video_title, functionalities, inference_data, output_dir, worker_thread=None
            )
        
        print("\n" + "="*70)
        print("WORKFLOW COMPLETE")
        print("="*70)
        print(f"✅ Total functionalities: {len(functionalities)}")
        print(f"✅ Document: {pdd_file}")
        print("="*70 + "\n")
        
        results = {
            "video_path": video_path,
            "document_path": doc_path,
            "total_frames": len(frame_data),
            "transcript_entries": len(transcript_data),
            "functionalities_count": len(functionalities),
            "pdd_document": pdd_file,
            "inference_data": inference_data
        }
        
        return results
    
    def find_closest_timestamp(self, target_seconds, transcript_data, direction="both"):
        """
        Find closest timestamp in transcript
        direction: "both" (exact or closest), "before" (for start), "after" (for end)
        """
        if not transcript_data:
            return None
        
        # Try exact match first
        for entry in transcript_data:
            if entry['time_seconds'] == target_seconds:
                return entry['time_seconds']
        
        # Find closest
        closest_entry = None
        min_diff = float('inf')
        
        for entry in transcript_data:
            diff = abs(entry['time_seconds'] - target_seconds)
            
            if direction == "before" and entry['time_seconds'] > target_seconds:
                continue  # Skip entries after target for start_split
            
            if direction == "after" and entry['time_seconds'] < target_seconds:
                continue  # Skip entries before target for end_split
            
            if diff < min_diff:
                min_diff = diff
                closest_entry = entry
        
        return closest_entry['time_seconds'] if closest_entry else None


    def filter_transcript_by_splits(self, transcript_data, split_json_path):
        """
        Filter transcript entries based on split timestamps from JSON
        Returns only transcript entries within split ranges
        """
        if not os.path.exists(split_json_path):
            print("⚠️ No split JSON found, using full transcript")
            return transcript_data
        
        try:
            with open(split_json_path, "r") as f:
                split_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading split JSON: {e}")
            return transcript_data
        
        if "videos" not in split_data:
            print("⚠️ Invalid split JSON format")
            return transcript_data
        
        filtered_transcript = []
        
        # Process each video's splits
        for video_idx, video_entry in enumerate(split_data["videos"]):
            video_name = video_entry.get("video_name", f"Video {video_idx+1}")
            splits = video_entry.get("splits", {})
            
            print(f"\n{'='*60}")
            print(f"Filtering transcript for: {video_name}")
            print(f"{'='*60}")
            
            if not splits:
                print(f"⚠️ No splits found for {video_name}, skipping")
                continue
            
            # Get transcript entries for this video
            video_transcript = [entry for entry in transcript_data if entry.get('video_index') == video_idx + 1]
            
            if not video_transcript:
                print(f"⚠️ No transcript found for {video_name}")
                continue
            
            # Process each split
            for split_key, split_info in splits.items():
                start_ms = split_info.get("start_ms", 0)
                end_ms = split_info.get("end_ms", 0)
                
                start_seconds = start_ms // 1000
                end_seconds = end_ms // 1000
                
                print(f"\n  {split_key}: {split_info['start_split']} → {split_info['end_split']}")
                print(f"  Target range: {start_seconds}s - {end_seconds}s")
                
                # Find closest start timestamp (prefer earlier or exact)
                actual_start = self.find_closest_timestamp(start_seconds, video_transcript, direction="before")
                if actual_start is None:
                    actual_start = self.find_closest_timestamp(start_seconds, video_transcript, direction="after")
                
                # Find closest end timestamp (prefer later or exact)
                actual_end = self.find_closest_timestamp(end_seconds, video_transcript, direction="after")
                if actual_end is None:
                    actual_end = self.find_closest_timestamp(end_seconds, video_transcript, direction="before")
                
                if actual_start is None or actual_end is None:
                    print(f"  ⚠️ Could not find matching timestamps")
                    continue
                
                print(f"  Actual range: {actual_start}s - {actual_end}s")
                
                # Filter entries within range
                split_entries = [
                    entry for entry in video_transcript
                    if actual_start <= entry['time_seconds'] <= actual_end
                ]
                
                print(f"  ✅ Found {len(split_entries)} transcript entries")
                
                filtered_transcript.extend(split_entries)
        
        print(f"\n{'='*60}")
        print(f"Total filtered entries: {len(filtered_transcript)} (out of {len(transcript_data)})")
        print(f"{'='*60}\n")
        
        return filtered_transcript if filtered_transcript else transcript_data
    
    def extract_additional_docs_content(self, additional_docs: List[str]) -> str:
        """
        Extract and format content from additional supporting documents
        Supports: .txt, .docx, .pdf, .doc
        """
        if not additional_docs:
            return ""
        
        all_content = []
        
        for doc_idx, doc_path in enumerate(additional_docs):
            if not os.path.exists(doc_path):
                print(f"⚠️ Additional doc not found: {doc_path}")
                continue
            
            file_name = os.path.basename(doc_path)
            file_ext = os.path.splitext(doc_path)[1].lower()
            
            try:
                content = ""
                
                # Extract based on file type
                if file_ext == '.txt':
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                elif file_ext == '.docx':
                    doc = docx.Document(doc_path)
                    content = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
                
                elif file_ext == '.pdf':
                    import PyPDF2
                    with open(doc_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        content = '\n'.join([page.extract_text() for page in pdf_reader.pages])
                
                elif file_ext == '.doc':
                    # Try converting .doc to .docx first
                    try:
                        from Word_Pdf_Converter import docx_to_pdf
                        # Create temp docx
                        temp_docx = doc_path.replace('.doc', '_temp.docx')
                        os.system(f'libreoffice --headless --convert-to docx "{doc_path}" --outdir "{os.path.dirname(doc_path)}"')
                        if os.path.exists(temp_docx):
                            doc = docx.Document(temp_docx)
                            content = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
                            os.remove(temp_docx)
                    except:
                        print(f"⚠️ Could not convert .doc file: {file_name}")
                        continue
                
                if content.strip():
                    # Format the content with document header
                    formatted_content = f"""
                    
    **ADDITIONAL SUPPORTING DOCUMENT {doc_idx + 1}: {file_name}**

    {content.strip()}

    ---
    """
                    all_content.append(formatted_content)
                    print(f"✅ Extracted content from: {file_name} ({len(content)} chars)")
                else:
                    print(f"⚠️ No content extracted from: {file_name}")
                    
            except Exception as e:
                print(f"❌ Error extracting {file_name}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        if all_content:
            combined = "\n".join(all_content)
            print(f"✅ Total additional docs processed: {len(all_content)}")
            return combined
        else:
            return ""


    def process_multiple_videos_and_transcripts(self, video_paths: list, transcript_paths: list,
                                            output_dir: str = "analysis_output",
                                            create_pdd: bool = True,
                                            crop_frames: bool = True,
                                            crop_right_percent: float = 0.13,
                                            worker_thread=None,
                                            custom_prompt: str = "",
                                            split_json_path: str = None,
                                            additional_docs_content: str = "",  # NEW PARAMETER
                                            **kwargs) -> dict:
        """
        Process multiple videos with their transcripts
        NOW INCLUDES: Additional supporting documents content
        1. Extract frames from all videos
        2. Parse all transcripts and COMBINE them
        3. Filter transcripts based on split_timestamps.json (if provided)
        4. Single API call with FILTERED transcript + ADDITIONAL DOCS
        5. Match frames to functionalities
        6. Show review dialog
        7. Create final document
        """
        print("\n" + "="*70)
        print(f"PROCESSING {len(video_paths)} VIDEOS WITH COMBINED TRANSCRIPTS")
        if additional_docs_content:
            print("📎 ADDITIONAL SUPPORTING DOCUMENTS INCLUDED")
        print("="*70)
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Store first video path for reference
        self._last_video_path = video_paths[0]

        # Convert all transcript paths to absolute paths
        transcript_paths = [os.path.abspath(path) for path in transcript_paths]
        
        # Validate all transcript files exist
        for idx, transcript_path in enumerate(transcript_paths):
            if not os.path.exists(transcript_path):
                raise FileNotFoundError(
                    f"Transcript file {idx+1} not found: {transcript_path}\n"
                    f"Current working directory: {os.getcwd()}"
                )
        
        # Step 1: Extract frames from ALL videos
        print(f"\nStep 1: Extracting frames from {len(video_paths)} video(s)...")
        all_frame_data = []
        
        for video_idx, video_path in enumerate(video_paths):
            print(f"\n  Processing video {video_idx+1}/{len(video_paths)}: {os.path.basename(video_path)}")
            frames_subdir = os.path.join(output_dir, f"frames_video_{video_idx+1}")
            
            frame_data = self.extract_frames_from_video(
                video_path,
                frames_subdir,
                crop_frames=crop_frames,
                crop_right_percent=crop_right_percent
            )
            
            # Add video index to each frame
            for frame in frame_data:
                frame['video_index'] = video_idx + 1
                frame['video_name'] = os.path.basename(video_path)
            
            all_frame_data.extend(frame_data)
            print(f"  ✅ Extracted {len(frame_data)} frames from video {video_idx+1}")
        
        print(f"\n✅ Total frames extracted: {len(all_frame_data)}")
        
        # Step 2: Parse ALL transcripts and COMBINE them
        print(f"\nStep 2: Parsing and combining {len(transcript_paths)} transcript(s)...")
        combined_transcript_data = []
        
        for trans_idx, transcript_path in enumerate(transcript_paths):
            print(f"\n  Parsing transcript {trans_idx+1}/{len(transcript_paths)}: {os.path.basename(transcript_path)}")
            
            transcript_data = self.parse_transcript_document(transcript_path)
            
            # Add video context to each transcript entry
            for entry in transcript_data:
                entry['video_index'] = trans_idx + 1
                entry['video_name'] = os.path.basename(video_paths[trans_idx]) if trans_idx < len(video_paths) else f"Video {trans_idx+1}"
            
            combined_transcript_data.extend(transcript_data)
            print(f"  ✅ Parsed {len(transcript_data)} entries from transcript {trans_idx+1}")
        
        print(f"\n✅ Combined transcript entries: {len(combined_transcript_data)}")
        
        # Step 2.5 - Filter transcript based on split_timestamps.json
        if split_json_path and os.path.exists(split_json_path):
            print(f"\nStep 2.5: Filtering transcript based on splits...")
            combined_transcript_data = self.filter_transcript_by_splits(
                combined_transcript_data, 
                split_json_path
            )
            print(f"✅ Filtered to {len(combined_transcript_data)} entries")
        else:
            print("\n⚠️ No split JSON provided, using full transcript")
        
        # Step 3: SINGLE API CALL with FILTERED transcript + ADDITIONAL DOCS
        print("\nStep 3: Comprehensive analysis with FILTERED transcript + ADDITIONAL DOCS (SINGLE API CALL)...")
        inference_data, functionalities = self.analyze_transcript_with_comprehensive_prompt(
            combined_transcript_data, 
            custom_prompt,
            additional_docs_content  # NEW: Pass additional docs content
        )
        
        if not functionalities:
            raise RuntimeError("No functionalities extracted from combined transcripts")
        
        # Step 4: Match frames to functionalities (using all frames)
        print("\nStep 4: Matching frames to functionalities...")
        functionalities = self.match_frames_to_functionalities(functionalities, all_frame_data)
        
        # Step 5: Show review dialog (if worker thread provided)
        if worker_thread is not None:
            print("\nStep 5: Showing review dialog...")
            worker_thread.show_review_dialog.emit(
                self, functionalities, video_paths[0], output_dir
            )
            
            final_functionalities = worker_thread.wait_for_review()
            
            if final_functionalities is None or len(final_functionalities) == 0:
                print("❌ User cancelled review")
                return {}
            
            functionalities = final_functionalities
            print(f"✅ User approved {len(functionalities)} functionalities")
        
        # Step 6: Create document
        pdd_file = None
        if create_pdd:
            print("\nStep 6: Creating PDD document...")
            # Use first video title or combine video names
            if len(video_paths) == 1:
                video_title = os.path.basename(video_paths[0]).split('.')[0].replace('-', ' ').replace('_', ' ')
            else:
                video_title = f"Combined_{len(video_paths)}_Videos"
            
            pdd_file = self.create_pdd_document(
                video_title, functionalities, inference_data, output_dir, worker_thread=None
            )
        
        print("\n" + "="*70)
        print("MULTI-VIDEO WORKFLOW COMPLETE")
        print("="*70)
        print(f"✅ Videos processed: {len(video_paths)}")
        print(f"✅ Total frames: {len(all_frame_data)}")
        print(f"✅ Total transcript entries: {len(combined_transcript_data)}")
        print(f"✅ Total functionalities: {len(functionalities)}")
        if additional_docs_content:
            print(f"✅ Additional docs integrated")
        print(f"✅ Document: {pdd_file}")
        print("="*70 + "\n")
        
        results = {
            "video_paths": video_paths,
            "transcript_paths": transcript_paths,
            "total_frames": len(all_frame_data),
            "total_transcript_entries": len(combined_transcript_data),
            "functionalities_count": len(functionalities),
            "pdd_document": pdd_file,
            "inference_data": inference_data
        }
        
        return results
    
    def upload_to_cloud(
        self,
        video_path: str,
        transcript_path: str,
        pdd_path: str,
        project_id: str,
        task_id: str,
        user_id: str,
        upload_url: str = "https://droidal.ai/app/project/upload-files/",
    ) -> dict:
        
        import tkinter as tk
        from tkinter import messagebox

        for name, path in [
            ("video", video_path),
            ("transcript", transcript_path),
            ("PDD document", pdd_path),
        ]:
            if not Path(path).is_file():
                raise FileNotFoundError(f"{name} not found: {path}")

        payload = {
            "user_id": user_id,
            "task_id": task_id,
            "project_id": project_id,
        }

        files = [
            ("files", ("source_video.mp4", open(video_path, "rb"), "video/mp4")),
            ("files", ("transcript.docx", open(transcript_path, "rb"),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ("files", ("PDD.docx", open(pdd_path, "rb"),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ]

        try:
            response = requests.post(upload_url, data=payload, files=files, timeout=180)
            response.raise_for_status()
        except requests.RequestException as exc:
            # ------------------------------------------------------
            #  USER-FRIENDLY POP-UP
            # ------------------------------------------------------
            root = tk.Tk()
            root.withdraw()                     # hide the empty window
            messagebox.showerror(
                "Upload Failed",
                "video not upload to cloud\n\n"
                f"Server returned: {response.status_code} {response.reason}\n"
                f"URL: {upload_url}"
            )
            root.destroy()

            # Keep the original traceback in the console for debugging
            raise RuntimeError(f"Upload failed: {exc}") from exc
        finally:
            for _, (fname, fobj, ctype) in files:
                fobj.close()

        try:
            return response.json()
        except ValueError:
            return {"raw_response": response.text}

def process_files(video_path: str, doc_path: str,
                  project_id: str, task_id: str, user_id: str, 
                  worker_thread=None, custom_prompt: str = "") -> str:  
    """
    Main entry point with custom prompt support
    """
    GEMINI_API_KEY = config.API_KEY
    CREATE_PDD = True
    
    analyzer = VideoTranscriptAnalyzer(GEMINI_API_KEY)
    
    results = analyzer.process_video_and_transcript(
        video_path, doc_path,
        create_pdd=CREATE_PDD,
        worker_thread=worker_thread,
        custom_prompt=custom_prompt  
    )
    
    pdd_path = results.get("pdd_document")
    if not pdd_path:
        raise RuntimeError("PDD generation failed")
    
    print("\nUploading to cloud...")
    upload_resp = analyzer.upload_to_cloud(
        video_path=video_path,
        transcript_path=doc_path,
        pdd_path=pdd_path,
        project_id=project_id,
        task_id=task_id,
        user_id=user_id,
    )
    
    print("Upload response:", upload_resp)
    return str(pdd_path)



def convert_multiple_videos_to_pdf(video_paths: list, transcript_paths: list,
                                project_id: str, task_id: str, user_id: str, 
                                worker_thread=None, custom_prompt: str = "",
                                split_json_path: str = None,
                                additional_docs: list = None) -> str:  # NEW PARAMETER
    """
    Process multiple videos with their transcripts
    NOW INCLUDES: Additional supporting documents
    All transcripts are COMBINED and FILTERED by splits before analysis
    """
    GEMINI_API_KEY = config.API_KEY
    CREATE_PDD = True
    
    analyzer = VideoTranscriptAnalyzer(GEMINI_API_KEY)
    
    # Extract content from additional docs (if provided)
    additional_docs_content = ""
    if additional_docs:
        print(f"\n📎 Processing {len(additional_docs)} additional document(s)...")
        additional_docs_content = analyzer.extract_additional_docs_content(additional_docs)
        if additional_docs_content:
            print(f"✅ Additional docs content ready ({len(additional_docs_content)} chars)")
        else:
            print("⚠️ No content extracted from additional docs")
    
    results = analyzer.process_multiple_videos_and_transcripts(
        video_paths, transcript_paths,
        create_pdd=CREATE_PDD,
        worker_thread=worker_thread,
        custom_prompt=custom_prompt,
        split_json_path=split_json_path,
        additional_docs_content=additional_docs_content  # NEW: Pass extracted content
    )
    
    pdd_path = results.get("pdd_document")
    if not pdd_path:
        raise RuntimeError("PDD generation failed")
    
    print("\nUploading to cloud...")
    upload_resp = analyzer.upload_to_cloud(
        video_path=video_paths[0],
        transcript_path=transcript_paths[0],
        pdd_path=pdd_path,
        project_id=project_id,
        task_id=task_id,
        user_id=user_id,
    )
    
    print("Upload response:", upload_resp)
    return str(pdd_path)

def convert_video_to_pdf(input_video_path, input_transcript_path, 
                        project_id, task_id, user_id, worker_thread=None,
                        custom_prompt=""):  
    return process_files(
        input_video_path,
        input_transcript_path,
        project_id,
        task_id,
        user_id,
        worker_thread=worker_thread,
        custom_prompt=custom_prompt 
    )