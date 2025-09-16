#!/usr/bin/env python3
"""
Test client for Zoom Transcript Task Extractor
Simulates Zoom RTMS sending transcript data via WebSocket
"""

import asyncio
import json
import websockets
import aiohttp
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample transcript messages that would come from Zoom
SAMPLE_TRANSCRIPTS = [
    {
        "participant_id": "user_001",
        "participant_name": "John Smith",
        "text": "Alright everyone, let's make sure John completes the quarterly financial report by Friday. This is high priority since we need it for the board meeting.",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "participant_id": "user_002", 
        "participant_name": "Sarah Johnson",
        "text": "I'll take care of updating the project documentation. Also, can someone schedule a follow-up meeting with the client for next week?",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "participant_id": "user_003",
        "participant_name": "Mike Davis", 
        "text": "The bug in the payment system needs to be fixed ASAP. Mike, can you look into this today? It's blocking our release.",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "participant_id": "user_001",
        "participant_name": "John Smith",
        "text": "Thanks everyone for the update. Let me know if you need any resources. The deadline is firm.",
        "timestamp": datetime.utcnow().isoformat()
    }
]

async def test_websocket_connection():
    """Test WebSocket connection and transcript processing"""
    uri = "ws://localhost:8000/ws/transcript"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send sample transcript messages
            for i, transcript in enumerate(SAMPLE_TRANSCRIPTS):
                logger.info(f"Sending transcript {i+1}: {transcript['participant_name']}")
                await websocket.send(json.dumps(transcript))
                
                # Wait for response
                response = await websocket.recv()
                result = json.loads(response)
                logger.info(f"Response: {result}")
                
                # Small delay between messages
                await asyncio.sleep(2)
                
    except Exception as e:
        logger.error(f"WebSocket connection failed: {e}")

async def test_tasks_endpoint():
    """Test the /tasks REST endpoint"""
    url = "http://localhost:8000/tasks"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    tasks = await response.json()
                    logger.info(f"Retrieved {len(tasks)} tasks from API")
                    
                    for i, task in enumerate(tasks, 1):
                        logger.info(f"Task {i}:")
                        logger.info(f"  Title: {task['title']}")
                        logger.info(f"  Description: {task['description']}")
                        logger.info(f"  Assignee: {task['assignee']}")
                        logger.info(f"  Priority: {task['priority']}")
                        logger.info(f"  Source: {task['source_participant']}")
                        logger.info("---")
                else:
                    logger.error(f"Failed to get tasks: {response.status}")
                    
    except Exception as e:
        logger.error(f"Failed to test tasks endpoint: {e}")

async def test_health_endpoint():
    """Test the health check endpoint"""
    url = "http://localhost:8000/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Health check: {result}")
                else:
                    logger.error(f"Health check failed: {response.status}")
                    
    except Exception as e:
        logger.error(f"Health check error: {e}")

async def main():
    """Run all tests"""
    logger.info("Starting test client...")
    
    # Test health endpoint first
    logger.info("Testing health endpoint...")
    await test_health_endpoint()
    await asyncio.sleep(1)
    
    # Test WebSocket transcript processing
    logger.info("Testing WebSocket transcript processing...")
    await test_websocket_connection()
    await asyncio.sleep(2)
    
    # Test tasks endpoint to see extracted tasks
    logger.info("Testing tasks endpoint...")
    await test_tasks_endpoint()
    
    logger.info("Test client finished")

if __name__ == "__main__":
    asyncio.run(main())