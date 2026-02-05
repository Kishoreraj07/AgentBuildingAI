import cv2
import os
import re
import docx
from datetime import datetime, timedelta
import google.generativeai as genai
import base64
from PIL import Image
import io
import ast
from typing import List, Dict, Tuple
from docx import Document
import json
from skimage.metrics import structural_similarity as ssim
import numpy as np
from docx.shared import Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datas.source_files import config
class VideoTranscriptAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the analyzer with Gemini API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    def clean_text_formatting(self, text: str) -> str:
        """
        Clean text by removing markdown formatting symbols and other unwanted characters
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text without formatting symbols
        """
        if not text:
            return ""
        
        # Remove markdown bold formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*\*', '', text)
        
        # Remove bullet point symbols
        text = re.sub(r'^[•·○]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[•·○]\s*', '', text, flags=re.MULTILINE)
        
        # Remove multiple bullet symbols
        text = re.sub(r'[•·○]+', '', text)
        
        # Clean up extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_frames_from_video(self, video_path: str, output_dir: str = "frames", ssim_threshold: float = 0.85, crop_frames: bool = True, crop_right_percent: float = 0.13) -> List[str]:
        """
        Extract frames from video when significant visual changes occur.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save extracted frames
            ssim_threshold: SSIM threshold below which a frame is considered different (0 to 1)
            crop_frames: Whether to crop frames to remove speaker panel
            crop_right_percent: Percentage of width to crop from right side (default 15%)
            
        Returns:
            List of frame file paths
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return []
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"Video FPS: {fps}")
        print(f"Total frames: {total_frames}")
        print(f"Duration: {duration:.2f} seconds")
        
        frame_paths = []
        prev_frame = None
        frame_count = 0
        second_count = 0
        frame_interval = int(fps / 5)  # Check 5 times per second for changes (adjustable)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process frame at specified interval
            if frame_count % frame_interval == 0:
                # Convert frame to grayscale for SSIM comparison
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # Compute SSIM between current and previous frame
                    similarity, _ = ssim(prev_frame, gray_frame, full=True)
                    
                    # If frames are sufficiently different (below threshold), save the frame
                    if similarity < ssim_threshold:
                        timestamp = frame_count / fps
                        frame_filename = f"frame_{second_count:04d}_{timestamp:.2f}s.jpg"
                        frame_path = os.path.join(output_dir, frame_filename)
                        
                        # Crop frame if requested
                        if crop_frames:
                            height, width = frame.shape[:2]
                            crop_width = int(width * (1 - crop_right_percent))
                            cropped_frame = frame[:, :crop_width]
                            cv2.imwrite(frame_path, cropped_frame)
                            print(f"Saved cropped frame at {frame_count/fps:.2f} seconds (SSIM: {similarity:.4f})")
                        else:
                            cv2.imwrite(frame_path, frame)
                            print(f"Saved frame at {frame_count/fps:.2f} seconds (SSIM: {similarity:.4f})")
                        
                        frame_paths.append(frame_path)
                        second_count += 1
                
                prev_frame = gray_frame
                
            frame_count += 1
            
        cap.release()
        print(f"Extracted {len(frame_paths)} frames based on visual changes")
        return frame_paths
        
   
    def parse_transcript_document(self, doc_path: str) -> List[Dict]:
        """
        Parse Word document transcript to extract timestamps and text
        
        Args:
            doc_path: Path to the Word document
            
        Returns:
            List of dictionaries with timestamp and text
        """
        doc = docx.Document(doc_path)
        transcript_data = []
        
        current_speaker = ""
        current_time = ""
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
                
            # Look for speaker names (bold text)
            if paragraph.runs:
                for run in paragraph.runs:
                    if run.bold and text:
                        current_speaker = text.replace('**', '')
                        break
                        
            # Look for timestamps (format: MM:SS or M:SS)
            time_pattern = r'\b(\d{1,2}:\d{2})\b'
            time_match = re.search(time_pattern, text)
            
            if time_match:
                current_time = time_match.group(1)
                # Remove timestamp from text
                text = re.sub(time_pattern, '', text).strip()
                
            # If we have both speaker and meaningful text, add to transcript
            if current_speaker and text and not re.match(r'^\d{1,2}:\d{2}$', text):
                transcript_data.append({
                    'timestamp': current_time,
                    'speaker': current_speaker,
                    'text': text,
                    'time_seconds': self._convert_to_seconds(current_time)
                })
                
        return transcript_data
        
    def _convert_to_seconds(self, time_str: str) -> int:
        """Convert MM:SS format to total seconds"""
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
        
    def match_frames_to_transcript(self, frame_paths: List[str], transcript_data: List[Dict]) -> List[Dict]:
        """
        Match video frames to transcript timestamps
        
        Args:
            frame_paths: List of frame file paths
            transcript_data: List of transcript entries
            
        Returns:
            List of matched frame-transcript pairs
        """
        matched_data = []
        
        for i, frame_path in enumerate(frame_paths):
            # Extract second from frame filename (e.g., frame_0001_12.34s.jpg -> 12.34 seconds)
            try:
                timestamp_match = re.search(r'(\d+\.\d+)s\.jpg', os.path.basename(frame_path))
                frame_second = float(timestamp_match.group(1)) if timestamp_match else i
            except:
                frame_second = i
            
            # Find closest transcript entry
            closest_transcript = None
            min_diff = float('inf')
            
            for transcript_entry in transcript_data:
                time_diff = abs(transcript_entry['time_seconds'] - frame_second)
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_transcript = transcript_entry
                    
            matched_data.append({
                'frame_path': frame_path,
                'frame_second': frame_second,
                'timestamp': f"{int(frame_second//60)}:{int(frame_second%60):02d}",
                'transcript': closest_transcript,
                'time_diff': min_diff
            })
            
        return matched_data
        
    def encode_image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 string for API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def analyze_frame_with_transcript(self, frame_path: str, transcript_text: str, context: str = "") -> str:
        """
        Analyze a single frame with its corresponding transcript using Gemini API
        
        Args:
            frame_path: Path to the frame image
            transcript_text: Corresponding transcript text
            context: Additional context about the meeting
            
        Returns:
            Analysis result
        """
        # Upload the image
        image = Image.open(frame_path)
        
        prompt = f"""
        Analyze this video frame along with the corresponding transcript text.
        
        Transcript text: "{transcript_text}"
        Context: "{context}"
        
        Please identify:
        1. What is being discussed or shown in the frame
        2. Any requirements, action items, or decisions mentioned
        3. Technical details or specifications
        4. Any UI elements, screens, or visual information
        5. Key points that relate to business processes or workflows
        
        Focus on extracting actionable requirements and business logic.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            return f"Error analyzing frame: {str(e)}"

    def analyze_frame_for_pdd(self, frame_path: str, frame_number: int, timestamp: float, transcript_text: str = "", context: str = "") -> Dict:
        """
        Analyze a single frame for PDD format using Gemini API
        
        Args:
            frame_path: Path to the frame image
            frame_number: Frame sequence number
            timestamp: Frame timestamp in seconds
            transcript_text: Corresponding transcript text
            context: Additional context about the meeting
            
        Returns:
            Dictionary with PDD analysis results
        """
        # Upload the image
        image = Image.open(frame_path)
        
        prompt = f"""
        Analyze this screenshot from a business process demonstration.
        
        Frame Number: {frame_number}
        Timestamp: {timestamp:.2f} seconds
        Transcript: "{transcript_text}"
        Context: "{context}"
        
        Provide a detailed step-by-step analysis for process documentation:
        
        STEP_TITLE: [Brief title describing the action being performed]
        SCREEN_DESCRIPTION: [Describe what application/screen is visible and its current state]
        ACTION_TO_PERFORM: [Specific action the user needs to perform - click, type, select, navigate, etc.]
        DETAILED_INSTRUCTIONS: [Step-by-step instructions a user should follow]
        BUSINESS_PURPOSE: [Why this step is important in the business process]
        TECHNICAL_NOTES: [Any technical details like field names, system names, data values, validation rules]
        
        Focus on creating clear, actionable instructions for process documentation.
        Be specific about UI elements, button names, field names, and exact steps.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            analysis_text = response.text
            
            # Parse the structured response
            analysis = {
                'frame_number': frame_number,
                'timestamp': timestamp,
                'frame_path': frame_path,
                'step_title': self.clean_text_formatting(self._extract_section(analysis_text, 'STEP_TITLE')),
                'screen_description': self.clean_text_formatting(self._extract_section(analysis_text, 'SCREEN_DESCRIPTION')),
                'action_to_perform': self.clean_text_formatting(self._extract_section(analysis_text, 'ACTION_TO_PERFORM')),
                'detailed_instructions': self.clean_text_formatting(self._extract_section(analysis_text, 'DETAILED_INSTRUCTIONS')),
                'business_purpose': self.clean_text_formatting(self._extract_section(analysis_text, 'BUSINESS_PURPOSE')),
                'technical_notes': self.clean_text_formatting(self._extract_section(analysis_text, 'TECHNICAL_NOTES')),
                'transcript_text': self.clean_text_formatting(transcript_text),
                'full_analysis': self.clean_text_formatting(analysis_text)
            }
            
            return analysis
            
        except Exception as e:
            return {
                'frame_number': frame_number,
                'timestamp': timestamp,
                'frame_path': frame_path,
                'error': f"Error analyzing frame: {str(e)}",
                'step_title': f'Step {frame_number}',
                'screen_description': '',
                'action_to_perform': '',
                'detailed_instructions': '',
                'business_purpose': '',
                'technical_notes': '',
                'transcript_text': self.clean_text_formatting(transcript_text),
                'full_analysis': ''
            }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract specific section from the analysis text"""
        try:
            pattern = f"{section_name}:\s*\\[?(.+?)\\]?\s*(?:\n\n|\n[A-Z_]+:|\n$|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        except:
            pass
        return ""

    def create_pdd_document(self, video_title: str, pdd_analyses: List[Dict], output_dir: str = "analysis_output") -> str:
        """Create a Process Design Document in Word format with frames and actions."""

        doc = Document()

        # Add document header
        header_table = doc.add_table(rows=1, cols=2)
        header_table.cell(0, 0).text = "5465 Legacy Drive, Suite 650, Plano Tx 75024\nwww.droidal.com"
        header_table.cell(0, 1).text = "AI AGENT\nProcess Design Document"
        header_table.cell(0, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # Add title
        doc.add_paragraph()
        title_para = doc.add_paragraph()
        title_run = title_para.add_run(self.clean_text_formatting(video_title))
        title_run.bold = True
        title_run.font.size = docx.shared.Pt(16)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add version
        version_para = doc.add_paragraph("Version 1.0")
        version_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_page_break()

        # Add process steps heading
        doc.add_heading('Process Steps:', level=1)

        # Add each step with screenshot and actions
        for analysis in pdd_analyses:
            try:
                # Create functionality heading
                step_title = analysis.get('step_title', f'Step {analysis["frame_number"]}')
                functionality_heading = f"Functionality #{analysis['frame_number']}: {self.clean_text_formatting(step_title)}"
                doc.add_heading(functionality_heading, level=2)

                # Add system/application info
                system_para = doc.add_paragraph()
                system_para.add_run("System/Application: ").bold = True
                system_para.add_run("Business Application")

                # Add step number and title in table format
                step_table = doc.add_table(rows=1, cols=2)
                step_table.cell(0, 0).text = str(analysis['frame_number'])
                step_table.cell(0, 0).width = Inches(0.5)

                # Add step content
                step_cell = step_table.cell(0, 1)
                step_title_para = step_cell.paragraphs[0]
                clean_step_title = self.clean_text_formatting(analysis.get('step_title', f'Process Step {analysis["frame_number"]}'))
                step_title_run = step_title_para.add_run(clean_step_title)
                step_title_run.bold = True

                # Add screenshot
                if os.path.exists(analysis['frame_path']):
                    screenshot_para = step_cell.add_paragraph()
                    screenshot_para.add_run("Screenshot:").bold = True
                    screenshot_para = step_cell.add_paragraph()
                    run = screenshot_para.add_run()
                    run.add_picture(analysis['frame_path'], width=Inches(5.5))

                # Add bullet points for actions
                action_text = analysis.get('action_to_perform', '')
                if action_text:
                    action_para = step_cell.add_paragraph()
                    action_para.add_run("The AI Agent performs the following steps:")

                    # Add main action as bullet point (cleaned)
                    clean_action = self.clean_text_formatting(action_text)
                    bullet_para = step_cell.add_paragraph(clean_action, style='List Bullet')

                    # Add detailed instructions as sub-bullets if available
                    detailed_instructions = analysis.get('detailed_instructions', '')
                    if detailed_instructions:
                        clean_instructions = self.clean_text_formatting(detailed_instructions)
                        instructions = clean_instructions.split('\n')
                        for instruction in instructions:
                            instruction = instruction.strip()
                            if instruction:
                                # Remove any remaining bullet symbols
                                clean_instruction = re.sub(r'^[•·○\-\*]\s*', '', instruction)
                                if clean_instruction:
                                    sub_bullet = step_cell.add_paragraph(clean_instruction, style='List Bullet')

                # Add technical notes if available
                technical_notes = analysis.get('technical_notes', '')
                if technical_notes:
                    clean_notes = self.clean_text_formatting(technical_notes)
                    if clean_notes:
                        note_para = step_cell.add_paragraph()
                        note_para.add_run("Note: ").bold = True
                        note_para.add_run(clean_notes)

                # Add screen description if available
                screen_description = analysis.get('screen_description', '')
                if screen_description:
                    clean_description = self.clean_text_formatting(screen_description)
                    if clean_description:
                        desc_para = step_cell.add_paragraph()
                        desc_para.add_run("Screen Details: ").bold = True
                        desc_para.add_run(clean_description)

                doc.add_paragraph()  # Add spacing

            except Exception as e:
                print(f"Error adding step {analysis['frame_number']} to PDD document: {str(e)}")
                error_para = doc.add_paragraph(f"Error processing step {analysis['frame_number']}: {str(e)}")

        # Save PDD document
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_video_title = self.clean_text_formatting(video_title.replace(' ', '_').replace('/', '_'))
        pdd_filename = f"PDD_{clean_video_title}_{timestamp_str}.docx"
        pdd_file = os.path.join(output_dir, pdd_filename)
        doc.save(pdd_file)

        print(f"PDD document saved to {pdd_file}")
        return pdd_file

    def extract_requirements_summary(self, analysis_results: List[str], full_transcript: str, output_dir: str = "analysis_output") -> str:
        """Generate a comprehensive requirements summary from all analysis results and save to a Word document."""

        combined_analysis = "\n\n".join(analysis_results)

        prompt = """
        Based on the following video frame analyses and transcript from a business meeting, extract and organize all requirements, action items, and key decisions as a sequence of development steps. Each step should be clear and actionable, describing tasks to implement the requirements. Use a format that lists steps like "launch: [url]", "click: [element]", "open: [resource]". Format the output for a Word document with headings and bullet points, without using a JSON structure.
        Frame Analyses:
        {combined_analysis}
        Full Transcript:
        {full_transcript}
        Please provide the output in the following format, suitable for a Word document:
        Development Steps
        Step-by-step tasks to implement requirements, e.g., 'launch: [url]', 'click: [element]', 'open: [resource]'
        Additional Points
        Any additional notes, constraints, or considerations for development
        Action Items
        Specific actions to be taken, assigned to individuals or teams
        Decisions Made
        Key decisions or agreements reached during the meeting
        Issues Identified
        Problems or challenges mentioned that may impact development
        Next Steps
        Follow-up actions or next steps for the project
        Key Stakeholders
        People mentioned and their roles, e.g., 'John Doe - Project Manager'
        Systems Mentioned
        Systems, APIs, or technologies discussed in the meeting
        """

        try:
            response = self.model.generate_content(prompt.format(combined_analysis=combined_analysis, full_transcript=full_transcript))
            result = response.text.strip()

            # Create Word document
            doc = Document()

            # Add headings and bullet points
            sections = [
                "Meeting Summary",
                "Development Steps",
                "Additional Points",
                "Action Items",
                "Decisions Made",
                "Issues Identified",
                "Next Steps",
                "Key Stakeholders",
                "Systems Mentioned"
            ]

            current_section = None
            for line in result.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Check if line is a heading
                if line in sections:
                    current_section = line
                    doc.add_heading(line, level=1)
                else:
                    # Clean the line before adding to document
                    clean_line = self.clean_text_formatting(line)
                    if clean_line:
                        # Add bullet point if original line had bullet formatting
                        if line.startswith('•') or line.startswith('·') or line.startswith('○') and current_section:
                            doc.add_paragraph(clean_line, style='List Bullet')
                        elif current_section:
                            doc.add_paragraph(clean_line)

            # Save to Word document
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_file = os.path.join(output_dir, "requirements_summary.docx")
            doc.save(output_file)

            print(f"Requirements summary saved to {output_file}")
            return result
        except Exception as e:
            error_result = f"Error generating summary: {str(e)}"
            # Save error to Word document
            doc = Document()
            doc.add_heading("Error", level=1)
            doc.add_paragraph(error_result)
            output_file = os.path.join(output_dir, "requirements_summary.docx")
            doc.save(output_file)
            print(f"Error saved to {output_file}")
            return error_result            
    def process_video_and_transcript(self, video_path: str, doc_path: str, output_dir: str = "analysis_output", ssim_threshold: float = 0.85, create_pdd: bool = True, crop_frames: bool = True, crop_right_percent: float = 0.13) -> Dict:
        """
        Main processing function that handles the entire workflow
        
        Args:
            video_path: Path to video file
            doc_path: Path to Word document transcript
            output_dir: Directory for output files
            ssim_threshold: SSIM threshold for frame difference detection
            create_pdd: Whether to create PDD document along with requirements summary
            crop_frames: Whether to crop frames to remove speaker panel
            crop_right_percent: Percentage of width to crop from right side (default 15%)
            
        Returns:
            Complete analysis results
        """
        print("Starting video and transcript analysis...")
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Step 1: Extract frames from video based on visual changes
        print("Extracting frames from video based on visual changes...")
        frame_paths = self.extract_frames_from_video(
            video_path, 
            os.path.join(output_dir, "frames"), 
            ssim_threshold,
            crop_frames,
            crop_right_percent
        )
        
        # Step 2: Parse transcript document
        print("Parsing transcript document...")
        transcript_data = self.parse_transcript_document(doc_path)
        
        # Step 3: Match frames to transcript
        print("Matching frames to transcript...")
        matched_data = self.match_frames_to_transcript(frame_paths, transcript_data)
        
        # Step 4: Analyze key frames with transcript
        print("Analyzing frames with transcript...")
        analysis_results = []
        pdd_analyses = []
        
        # Analyze all frames since they represent significant changes
        for i, data in enumerate(matched_data):
            transcript_text = data['transcript']['text'] if data['transcript'] else ""
            
            # Regular analysis for requirements summary
            if transcript_text:  # Only analyze frames with meaningful transcript
                analysis = self.analyze_frame_with_transcript(
                    data['frame_path'], 
                    transcript_text,
                    "This is from a business meeting about EOB (Explanation of Benefits) processing and API integration"
                )
                analysis_results.append(analysis)
                print(f"Analyzed frame at {data['timestamp']}")
            
            # PDD analysis for process documentation
            if create_pdd:
                pdd_analysis = self.analyze_frame_for_pdd(
                    data['frame_path'],
                    i + 1,
                    data['frame_second'],
                    transcript_text,
                    "EOB processing workflow demonstration"
                )
                pdd_analyses.append(pdd_analysis)
                print(f"PDD analysis completed for frame {i + 1}")
                
        # Step 5: Generate requirements summary
        print("Generating requirements summary...")
        full_transcript = "\n".join([entry['text'] for entry in transcript_data])
        requirements_summary = self.extract_requirements_summary(analysis_results, full_transcript, output_dir)
        
        # Step 6: Create PDD document if requested
        pdd_file = None
        if create_pdd and pdd_analyses:
            print("Creating PDD document...")
            video_title = os.path.basename(video_path).split('.')[0].replace('-', ' ').replace('_', ' ')
            pdd_file = self.create_pdd_document(video_title, pdd_analyses, output_dir)
        
        # Step 7: Save results
        results = {
            "video_path": video_path,
            "document_path": doc_path,
            "total_frames": len(frame_paths),
            "transcript_entries": len(transcript_data),
            "analysis_count": len(analysis_results),
            "pdd_analyses_count": len(pdd_analyses) if create_pdd else 0,
            "requirements_summary": requirements_summary,
            "pdd_document": pdd_file,
            "matched_data": matched_data[:5],  # Save first 5 for reference
            "frame_analyses": analysis_results[:3]  # Save first 3 for reference
        }
        
        # Save to JSON file
        output_file = os.path.join(output_dir, "analysis_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"Analysis complete. Results saved to {output_file}")
        return results

# Usage example
def main(VIDEO_PATH,DOCUMENT_PATH):
    # Configuration
    GEMINI_API_KEY = config.API_KEY # Replace with your Gemini API key
    # VIDEO_PATH = r"C:\Users\Deepakkumar.b\Downloads\RND Requirements call-20250902_200351-Meeting Recording.mp4"
    # DOCUMENT_PATH = r"C:\Users\Deepakkumar.b\Downloads\RND Requirements call-20250902_200351-Meeting Recording-en-IN.docx"
    SSIM_THRESHOLD = 0.85  # Adjust threshold for sensitivity (lower = more sensitive to changes)
    CREATE_PDD = True  # Set to True to create PDD document along with requirements summary
    
    # Initialize analyzer
    analyzer = VideoTranscriptAnalyzer(GEMINI_API_KEY)
    
    try:
        # Process video and transcript
        results = analyzer.process_video_and_transcript(
            VIDEO_PATH, 
            DOCUMENT_PATH, 
            ssim_threshold=SSIM_THRESHOLD,
            create_pdd=CREATE_PDD
        )
        
        # Print requirements summary
        print("\n" + "="*50)
        print("ANALYSIS SUMMARY")
        print("="*50)
        print(f"Total frames analyzed: {results['total_frames']}")
        print(f"Requirements summary: {results.get('requirements_summary', 'N/A')[:200]}...")
        if results.get('pdd_document'):
            print(f"PDD document created: {results['pdd_document']}")
        print("="*50)
            
    except Exception as e:
        print(f"Error in main processing: {str(e)}")


# if __name__ == "__main__":
#     # main()