from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import json
import logging
import os
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import openai
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="Zoom Transcript Task Extractor",
    description="Extracts tasks from Zoom live transcripts using LLM",
    version="1.0.0"
)

@dataclass
class Task:
    """Represents an extracted task from transcript"""
    id: str
    title: str
    description: str
    assignee: Optional[str] = None
    priority: str = "medium"
    created_at: str = None
    source_participant: str = ""
    source_text: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

class TranscriptMessage(BaseModel):
    """Represents incoming transcript message from Zoom"""
    participant_id: str
    participant_name: str
    text: str
    timestamp: str
    
class ConnectionManager:
    """Manages WebSocket connections"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")

class TaskExtractor:
    """Handles task extraction from transcript text using LLM or fallback rules"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = self.openai_api_key and self.openai_api_key != "test_key_for_demo"
        
        if self.use_openai:
            try:
                self.client = openai.OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.use_openai = False
        else:
            logger.info("Using fallback rule-based task extraction (no OpenAI API key)")
        
    async def extract_tasks_with_openai(self, text: str, participant_name: str) -> List[Task]:
        """Extract tasks using OpenAI API"""
        try:
            prompt = f"""
            Analyze the following meeting transcript from participant "{participant_name}" and extract any actionable tasks, assignments, or to-do items.
            
            Text: "{text}"
            
            Return a JSON array of tasks. Each task should have:
            - title: Brief task title
            - description: Detailed description
            - assignee: Person assigned (if mentioned, otherwise null)
            - priority: "high", "medium", or "low" based on urgency indicators
            
            Only return tasks that are clearly actionable. If no tasks are found, return an empty array.
            
            Example output:
            [
                {{
                    "title": "Prepare quarterly report",
                    "description": "Create Q4 financial summary with revenue analysis",
                    "assignee": "John",
                    "priority": "high"
                }}
            ]
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting actionable tasks from meeting transcripts. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                tasks_data = json.loads(content)
                if not isinstance(tasks_data, list):
                    logger.warning(f"LLM returned non-list response: {content}")
                    return []
                
                tasks = []
                for i, task_data in enumerate(tasks_data):
                    task = Task(
                        id=f"{participant_name}_{datetime.utcnow().timestamp()}_{i}",
                        title=task_data.get("title", "Unknown Task"),
                        description=task_data.get("description", ""),
                        assignee=task_data.get("assignee"),
                        priority=task_data.get("priority", "medium"),
                        source_participant=participant_name,
                        source_text=text
                    )
                    tasks.append(task)
                
                logger.info(f"Extracted {len(tasks)} tasks using OpenAI from {participant_name}")
                return tasks
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.error(f"Raw response: {content}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting tasks with OpenAI: {e}")
            return []

    async def extract_tasks_with_rules(self, text: str, participant_name: str) -> List[Task]:
        """Extract tasks using simple rule-based approach as fallback"""
        import re
        
        tasks = []
        text_lower = text.lower()
        
        # Task keywords and patterns
        task_indicators = [
            "нужно", "надо", "необходимо", "следует", "должен", "должна", "должны",
            "сделать", "выполнить", "подготовить", "завершить", "закончить",
            "need to", "have to", "must", "should", "complete", "finish", "prepare",
            "action item", "todo", "task", "assignment", "deadline"
        ]
        
        # Priority indicators
        high_priority = ["срочно", "asap", "urgent", "критично", "важно", "немедленно", "сегодня", "сейчас"]
        low_priority = ["когда будет время", "не спешно", "когда удобно", "later", "when convenient"]
        
        # Check if text contains task indicators
        has_task_indicator = any(indicator in text_lower for indicator in task_indicators)
        
        if has_task_indicator:
            # Determine priority
            priority = "medium"
            if any(hp in text_lower for hp in high_priority):
                priority = "high"
            elif any(lp in text_lower for lp in low_priority):
                priority = "low"
            
            # Try to extract assignee
            assignee = None
            # Look for names after task indicators
            name_patterns = [
                r"(?:должен|должна|нужно|надо)\s+(\w+)",
                r"(\w+)\s+(?:сделает|выполнит|подготовит)",
                r"assign(?:ed)?\s+to\s+(\w+)",
                r"(\w+)\s+will\s+(?:do|complete|prepare)"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    assignee = match.group(1).title()
                    break
            
            # Create task
            task_title = text[:50] + "..." if len(text) > 50 else text
            task = Task(
                id=f"{participant_name}_{datetime.utcnow().timestamp()}_0",
                title=f"Task from transcript: {task_title}",
                description=text,
                assignee=assignee,
                priority=priority,
                source_participant=participant_name,
                source_text=text
            )
            tasks.append(task)
            
            logger.info(f"Extracted {len(tasks)} tasks using rules from {participant_name}")
        
        return tasks
        
    async def extract_tasks(self, text: str, participant_name: str) -> List[Task]:
        """Extract tasks using OpenAI if available, otherwise fallback to rules"""
        if self.use_openai:
            return await self.extract_tasks_with_openai(text, participant_name)
        else:
            return await self.extract_tasks_with_rules(text, participant_name)

# Global instances
connection_manager = ConnectionManager()
task_extractor = TaskExtractor()
extracted_tasks: List[Task] = []

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "active", 
        "service": "Zoom Transcript Task Extractor",
        "llm_mode": "OpenAI" if task_extractor.use_openai else "Rule-based",
        "total_tasks": len(extracted_tasks)
    }

@app.get("/tasks", response_model=List[Dict[str, Any]])
async def get_tasks():
    """Get all extracted tasks as JSON array"""
    try:
        tasks_dict = [asdict(task) for task in extracted_tasks]
        logger.info(f"Returning {len(tasks_dict)} tasks")
        return tasks_dict
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")

@app.delete("/tasks")
async def clear_tasks():
    """Clear all extracted tasks"""
    global extracted_tasks
    count = len(extracted_tasks)
    extracted_tasks.clear()
    logger.info(f"Cleared {count} tasks")
    return {"message": f"Cleared {count} tasks"}

@app.websocket("/ws/transcript")
async def websocket_transcript_endpoint(websocket: WebSocket):
    """WebSocket endpoint for receiving live Zoom transcripts"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Receive transcript data from Zoom
            data = await websocket.receive_text()
            logger.info(f"Received transcript data: {data[:100]}...")
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                transcript_message = TranscriptMessage(**message_data)
                
                # Extract tasks from transcript
                new_tasks = await task_extractor.extract_tasks(
                    transcript_message.text, 
                    transcript_message.participant_name
                )
                
                # Add new tasks to global list
                extracted_tasks.extend(new_tasks)
                
                # Send confirmation back to client
                response = {
                    "status": "processed",
                    "participant": transcript_message.participant_name,
                    "tasks_extracted": len(new_tasks),
                    "total_tasks": len(extracted_tasks),
                    "llm_mode": "OpenAI" if task_extractor.use_openai else "Rule-based"
                }
                await websocket.send_text(json.dumps(response))
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
            except Exception as e:
                logger.error(f"Error processing transcript: {e}")
                await websocket.send_text(json.dumps({"error": "Processing failed"}))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )