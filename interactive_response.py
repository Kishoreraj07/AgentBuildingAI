import google.generativeai as genai
import json
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    VALIDATION_START = "validation_start"
    VALIDATION_PROGRESS = "validation_progress"
    VALIDATION_SUCCESS = "validation_success"
    VALIDATION_ERROR = "validation_error"
    TASK_CORRECTION_NEEDED = "task_correction_needed"
    TASK_CORRECTION_SUCCESS = "task_correction_success"
    DETAIL_MODE_INTRO = "detail_mode_intro"
    ELEMENT_FOUND="element_found"
    ELEMENT_CHECK = "element_check"
    VERIFY_MODIFY = "verify_modify"
    VERIFY_TRIGGERS = "verify_trigger"
    VERIFY_SUCCESS = "verify_success"
    VERIFY_ERROR = "verify_error"
    CHAT_WINDOW="chat_window"
    ENCOURAGEMENT = "encouragement"
    COMPLETION = "completion"

@dataclass
class ConversationContext:
    user_name: str = "User"
    session_id: str = ""
    task_count: int = 0
    current_task: int = 0
    validation_errors: int = 0
    successful_validations: int = 0
    session_start_time: float = 0
    user_preferences: Dict[str, Any] = None

class GeminiSessionService:
    """
    Gemini Session Service for maintaining conversation history and generating
    interactive, user-friendly messages throughout the task validation process.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite-exp"):
        """Initialize the Gemini session service"""
        try:
            genai.configure(api_key=api_key)
            
            # Define system instruction BEFORE creating the model
            self.system_instruction = """
You are an AI assistant for end-to-end task workflows: validation, detailing, verification, modification, restructuring, clarification, summarization, and guidance.

Your role is to:

1. Transform technical system messages into SHORT, warm, conversational messages (MAX 15 words)
2. Maintain a positive, supportive tone but be BRIEF
3. Use varied, non-repetitive language but keep it CONCISE
4. Provide clear, SHORT feedback when tasks need correction
5. Celebrate successes briefly but warmly
6. Be professional yet personable but ALWAYS CONCISE
7. You are not a robot, so avoid robotic phrases. Talk like a natural human with friendly tone.
8. You are telling the user what is happening in a friendly way.

Key guidelines:
- Use varied expressions to avoid repetition
- Keep messages concise but warm
- Maintain conversation flow and context        

CRITICAL: ALL messages must be 15 words or less. Be friendly but SHORT.

You should respond with JSON format containing:
{
    "message": "The SHORT user-friendly message (MAX 15 words)"
}
"""
            
            # Create model WITH system instruction
            self.model = genai.GenerativeModel(
                model_name, 
                system_instruction=self.system_instruction
            )
            
            self.chat_session = None
            self.conversation_history = []
            self.context = ConversationContext()
            self.message_variations = {}
            
            # Initialize the session
            self._initialize_session()
            self._load_message_templates()
            
            print("✅ Gemini Session Service initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing Gemini Session Service: {e}")
            raise
    
    def _initialize_session(self):
        """Initialize the chat session"""
        try:
            # Start chat session - system instruction is already set in the model
            self.chat_session = self.model.start_chat(history=[])
            self.context.session_start_time = time.time()
            
            print("🚀 Gemini chat session initialized with system instructions")
            
        except Exception as e:
            print(f"❌ Error initializing chat session: {e}")
            raise
    
    def _load_message_templates(self):
        """Load message template variations to ensure diversity"""
        self.message_variations = {
            MessageType.VALIDATION_START: [
                "Let's dive into validating your tasks! This won't take long.",
                "Time to check your tasks! I'll make sure everything looks perfect.",
                "Hey there! Let me quickly validate these tasks for you.",
                "Alright, let's review your tasks together! Just a moment please.",
                "Starting the validation process! I'll be thorough but quick."
            ],
            MessageType.VALIDATION_PROGRESS: [
                "Making great progress! Checking task {current} of {total}.",
                "Looking good so far! Now validating task {current}.",
                "Halfway there! Currently reviewing task {current}.",
                "Smooth sailing! Validating task {current} now.",
                "Almost done! Working on task {current} of {total}."
            ],
            MessageType.VALIDATION_SUCCESS: [
                "Excellent! All your tasks look perfect!",
                "Amazing work! Every task passed validation.",
                "Fantastic! All tasks are ready to go.",
                "Perfect! Your tasks are all set for execution.",
                "Outstanding! Everything validated successfully."
            ]
        }
    
    def update_context(self, **kwargs):
        """Update the conversation context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, str]:
        # Remove markdown code blocks if present
        cleaned_text = response_text.strip()
        
        # Handle ```json ``` blocks
        if cleaned_text.startswith('```json'):
            # Find the start and end of the JSON block
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned_text = cleaned_text[start_idx:end_idx + 1]
            else:
                raise ValueError("Could not find valid JSON in markdown block")
        
        elif cleaned_text.startswith('```'):
            lines = cleaned_text.split('\n')
            json_lines = []
            in_code_block = False
            
            for line in lines:
                if line.strip().startswith('```') and not in_code_block:
                    in_code_block = True
                    continue
                elif line.strip().startswith('```') and in_code_block:
                    break
                elif in_code_block:
                    json_lines.append(line)
            
            cleaned_text = '\n'.join(json_lines).strip()
        
        if '{' in cleaned_text and '}' in cleaned_text:
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned_text = cleaned_text[start_idx:end_idx + 1]
        
        # Parse the cleaned JSON
        try:
            result = json.loads(cleaned_text)
            
            # Validate that we have the expected structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a JSON object")
            
            # Ensure required fields exist
            if "message" not in result:
                result["message"] = cleaned_text.strip()
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON after cleaning: {e}")
            print(f"Cleaned text: {cleaned_text[:200]}...")
            raise

    def get_interactive_message(self, message_type: MessageType, 
                              system_message: str = "", 
                              **context_vars) -> Dict[str, str]:
        try:
            # Update context with any new variables
            self.update_context(**context_vars)
            
            # Create the prompt for Gemini
            prompt = self._create_message_prompt(message_type, system_message, **context_vars)
            
            # Send to Gemini
            response = self.chat_session.send_message(prompt)
            
            # Parse response
            try:
                result = self._extract_json_from_response(response.text)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON parsing failed: {e}")
                # Fallback if JSON parsing fails
                result = {
                    "message": response.text.strip()[:100]  # Limit fallback length
                }
            
            # Store in conversation history
            self.conversation_history.append({
                "timestamp": time.time(),
                "type": message_type.value,
                "prompt": prompt,
                "response": result,
                "context": dict(context_vars)
            })
            
            return result
            
        except Exception as e:
            print(f"❌ Error generating interactive message: {e}")
            # Fallback to template message
            return self._get_fallback_message(message_type, **context_vars)
    
    def _create_message_prompt(self, message_type: MessageType, 
                             system_message: str, **context_vars) -> str:
        """Create a detailed prompt for message generation"""
        
        base_context = f"""
Current context:
- Session duration: {time.time() - self.context.session_start_time:.1f} seconds
- Total tasks: {self.context.task_count}
- Current task: {self.context.current_task}
- Successful validations: {self.context.successful_validations}
- Validation errors: {self.context.validation_errors}
- Message type: {message_type.value}
"""
        
        if context_vars:
            base_context += f"\nAdditional context: {json.dumps(context_vars, indent=2)}"
        
        if system_message:
            base_context += f"\nOriginal system message: '{system_message}'"
        
        prompts = {
            MessageType.VALIDATION_START: f"""
{base_context}

Generate a warm, friendly message to inform the user that task validation is starting and hold on for few minutes.
Make it sound personal and engaging, not robotic. Keep it too short, it's just an start message.
Avoid repetitive phrases from previous messages in this session.
""",
            
            MessageType.VALIDATION_PROGRESS: f"""
{base_context}

Create an encouraging progress update message. The user should feel that things are going well
and that we're making good progress. Keep it brief but motivating.
Make it different from previous progress messages in this session.
""",
            
            MessageType.TASK_CORRECTION_NEEDED: f"""
{base_context}

You are writing a friendly, supportive message to the user.
Explain that the current task just needs a little refinement — this is normal and easy to fix.
Encourage collaboration rather than implying failure.

If the system message mentions a missing or unclear detail, politely ask for it
(e.g., “hey, looks like the URL is missing — could you provide it?”),
but let your own wording be natural and conversational.

Tone: warm, encouraging, collaborative.  
Avoid sounding robotic or formulaic and Keep it short.
Make it different from previous task correction messages in this session.
""",
            
            MessageType.VALIDATION_SUCCESS: f"""
{base_context}

Create a friendly message for successful validation completion. Keep it short, it's just an success message
Make it different from previous validation success messages in this session.
""",
            
            MessageType.DETAIL_MODE_INTRO: f"""
{base_context}

Generate a friendly introduction for the detail mode correction interface.
Explain what's happening in a conversational way and guide the user on what to do next.
Make it sound helpful and supportive, not intimidating.
Make it different from previous detail mode messages in this session.
""",

            MessageType.ELEMENT_FOUND: f"""
{base_context}  

Generate a friendly message informing the user that the specified element has been found.
Make it sound positive and reassuring, keeping the message concise and clear.
Make it different from previous element found messages in this session.
""",

            MessageType.ELEMENT_CHECK: f"""
{base_context}  

Generate a friendly message asking the user that the highlighting element is correct or not.
Make it sound positive and questioning, keeping the message concise and clear.
Make it different from previous element found messages in this session.
""",
            MessageType.VERIFY_TRIGGERS: f"""
{base_context}  

Generate a friendly message informing the user that the current task execution is correct or not.
Make it sound positive and reassuring, keeping the message concise and clear.
Make it different from previous verification messages in this session.
""",
            MessageType.VERIFY_MODIFY: f"""
{base_context}  

Generate a friendly message informing the user to provide the current tasks modification.
Make it sound positive and reassuring, keeping the message concise and clear.
Make it different from previous modification messages in this session.
""",
            MessageType.VERIFY_SUCCESS: f"""
{base_context}  

Generate a friendly message informing the user that the current task execution is correct.
Make it sound positive and reassuring, keeping the message concise and clear.
Make it different from previous success messages in this session.
""",
            MessageType.VERIFY_ERROR: f"""
{base_context}  

Generate a friendly message informing the user that the current task execution is incorrect.
Make it sound helpful and supportive, not intimidating.
Make it different from previous error messages in this session.
""",
            MessageType.CHAT_WINDOW: f"""
{base_context}  

Generate a friendly message informaing the user about the task that executed right now based on the user message. Sound it like it is Done
Make it sound positive and helpful.
Make it different from previous chat messages in this session
"""
        }

        
        return prompts.get(message_type, f"{base_context}\nGenerate a friendly, appropriate message for this situation.")
    
    def _get_fallback_message(self, message_type: MessageType, **context_vars) -> Dict[str, str]:
        """Provide fallback messages if Gemini is unavailable"""
        fallback_messages = {
            MessageType.VALIDATION_START: {
                "message": random.choice(self.message_variations[MessageType.VALIDATION_START])
            },
            MessageType.VALIDATION_PROGRESS: {
                "message": random.choice(self.message_variations[MessageType.VALIDATION_PROGRESS]).format(
                    current=context_vars.get('current_task', self.context.current_task),
                    total=context_vars.get('total_tasks', self.context.task_count)
                )
            },
            MessageType.VALIDATION_SUCCESS: {
                "message": random.choice(self.message_variations[MessageType.VALIDATION_SUCCESS])
            }
        }
        
        return fallback_messages.get(message_type, {
            "message": "Let's continue with the process!"
        })
    
    def get_task_correction_message(self, task_index: int, task_name: str, 
                                  validation_response: str) -> Dict[str, str]:
        """Generate a specific message for task correction"""
        return self.get_interactive_message(
            MessageType.TASK_CORRECTION_NEEDED,
            system_message=validation_response,
            task_index=task_index,
            task_name=task_name,
            current_task=task_index + 1
        )
    
    def get_validation_start_message(self, total_tasks: int) -> Dict[str, str]:
        """Generate validation start message"""
        self.update_context(task_count=total_tasks)
        return self.get_interactive_message(
            MessageType.VALIDATION_START,
            total_tasks=total_tasks
        )
    
    def get_chat_window_message(self,message : str) -> Dict[str,str]:
        self.update_context(message=message)
        return self.get_interactive_message(
            MessageType.CHAT_WINDOW,
            message=message
        )
    
    def get_validation_progress_message(self, current_task: int, total_tasks: int) -> Dict[str, str]:
        """Generate validation progress message"""
        self.update_context(current_task=current_task)
        return self.get_interactive_message(
            MessageType.VALIDATION_PROGRESS,
            current_task=current_task,
            total_tasks=total_tasks
        )
    
    def get_validation_success_message(self) -> Dict[str, str]:
        """Generate validation completion success message"""
        self.update_context(successful_validations=self.context.task_count)
        return self.get_interactive_message(MessageType.VALIDATION_SUCCESS)
    
    def get_detail_mode_intro_message(self, task_index: int, task_name: str) -> Dict[str, str]:
        """Generate detail mode introduction message"""
        return self.get_interactive_message(
            MessageType.DETAIL_MODE_INTRO,
            task_index=task_index,
            task_name=task_name,
            current_task=task_index + 1
        )
    
    def get_element_check_message(self) -> Dict[str, str]:
        """Generate element found message"""
        return self.get_interactive_message(
            MessageType.ELEMENT_CHECK
        )
    
    def get_verify_success_message(self) -> Dict[str, str]:
        """Generate verify success message"""
        return self.get_interactive_message(
            MessageType.VERIFY_SUCCESS
        )
        
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation session"""
        return {
            "session_duration": time.time() - self.context.session_start_time,
            "total_messages": len(self.conversation_history),
            "context": self.context.__dict__,
            "message_types_used": list(set(msg["type"] for msg in self.conversation_history))
        }
    
    def reset_session(self):
        """Reset the session for a new validation process"""
        self.conversation_history.clear()
        self.context = ConversationContext()
        self.context.session_start_time = time.time()
        
        # Start a new chat session
        self._initialize_session()
        
        print("🔄 Gemini session reset successfully")


# Example usage and integration helper
class GeminiMessageManager:
    """Helper class to manage Gemini messages in the application"""
    
    def __init__(self, api_key: str):
        self.gemini_service = GeminiSessionService(api_key)
    
    def get_friendly_message(self, message_type: str, **kwargs) -> str:
        """Get a friendly message and return just the text"""
        try:
            msg_type = MessageType(message_type)
            response = self.gemini_service.get_interactive_message(msg_type, **kwargs)
            return response.get("message", "Let's continue!")
        except Exception as e:
            print(f"Error getting friendly message: {e}")
            return "Let's keep going!"