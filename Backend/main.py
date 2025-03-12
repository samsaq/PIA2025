from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from hume import HumeStreamClient
from hume.models.config import LanguageConfig, ProsodyConfig, FaceConfig
import json
import random
from mistralai.client import MistralClient
from mistralai.models.chat import ChatMessage
import asyncio
import time

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Hume client
HUME_API_KEY = os.getenv("HUME_API_KEY")
hume_client = HumeStreamClient(HUME_API_KEY)

# Initialize Mistral client
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

# Store agents and their states
agents = []
current_conversations = {}

class Agent(BaseModel):
    id: str
    personality: str
    current_emotion: Dict[str, float] = {}
    conversation_history: List[Dict] = []

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# We'll add the specific endpoints below
# 1. Audio transcription endpoint
@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)

        # Configure Hume for speech-to-text
        config = ProsodyConfig(transcription=True)
        job = await hume_client.submit_file(file_path, [config])
        
        # Get results
        results = []
        async for result in job.stream():
            results.append(result)
        
        # Clean up temp file
        os.remove(file_path)
        
        # Extract transcription
        transcription = results[0]["prosody"]["predictions"][0]["text"]
        return {"transcription": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Audio emotion analysis endpoint
@app.post("/api/analyze-audio-emotion")
async def analyze_audio_emotion(file: UploadFile = File(...)):
    try:
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)

        config = ProsodyConfig(identify_speakers=True)
        job = await hume_client.submit_file(file_path, [config])
        
        results = []
        async for result in job.stream():
            results.append(result)
        
        os.remove(file_path)
        
        # Extract emotion scores
        emotions = results[0]["prosody"]["predictions"][0]["emotions"]
        return {"emotions": emotions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Video emotion analysis endpoint
@app.post("/api/analyze-video-emotion")
async def analyze_video_emotion(file: UploadFile = File(...)):
    try:
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)

        config = FaceConfig()
        job = await hume_client.submit_file(file_path, [config])
        
        results = []
        async for result in job.stream():
            results.append(result)
        
        os.remove(file_path)
        
        # Extract face emotion predictions
        emotions = results[0]["face"]["predictions"][0]["emotions"]
        return {"emotions": emotions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to generate random personality
def generate_personality():
    personalities = [
        "You are a curious student who loves asking deep questions about technology and innovation.",
        "You are a skeptical researcher who needs concrete evidence to be convinced.",
        "You are an enthusiastic learner who gets excited about new ideas.",
        "You are a practical thinker who focuses on real-world applications.",
        "You are a creative mind who likes to explore unconventional perspectives.",
        "You are a detail-oriented analyst who pays attention to specifics.",
        "You are a big-picture thinker who connects different concepts.",
        "You are a friendly student who enjoys collaborative learning.",
        "You are a challenging thinker who likes to debate ideas.",
        "You are an empathetic listener who considers emotional aspects."
    ]
    return random.choice(personalities)

# 4. Create random population of agents
@app.post("/api/create-agents")
async def create_agents():
    try:
        global agents
        agents = []
        for i in range(15):
            agent = Agent(
                id=f"agent_{i}",
                personality=generate_personality(),
                current_emotion={},
                conversation_history=[]
            )
            agents.append(agent)
        return {"agents": [agent.dict() for agent in agents]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Update agents with new emotion data and get responses
@app.post("/api/update-agents")
async def update_agents(data: Dict):
    try:
        emotion_data = data.get("emotion_data", {})
        transcribed_text = data.get("transcribed_text", "")
        
        responses = []
        # Randomly select 1-2 agents to respond
        responding_agents = random.sample(agents, random.randint(1, 2))
        
        for agent in responding_agents:
            # Update agent's emotion data
            agent.current_emotion = emotion_data
            
            # Create prompt for Mistral
            prompt = f"{agent.personality}\n\nCurrent context: {transcribed_text}\n"
            if agent.current_emotion:
                prompt += f"\nSpeaker's emotional state: {json.dumps(agent.current_emotion)}\n"
            prompt += "\nBased on your personality and the current context, express your thoughts or interest level in a brief response."
            
            # Get response from Mistral
            chat_response = mistral_client.chat(
                model="mistral-small-latest",
                messages=[ChatMessage(role="user", content=prompt)],
            )
            
            response = chat_response.messages[0].content
            agent.conversation_history.append({
                "text": transcribed_text,
                "emotion": emotion_data,
                "response": response
            })
            
            responses.append({
                "agent_id": agent.id,
                "response": response
            })
        
        return {"responses": responses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Generate questions from agents
@app.post("/api/generate-questions")
async def generate_questions():
    try:
        questions = []
        for agent in agents:
            prompt = f"{agent.personality}\n\nBased on the conversation history and your personality, generate an interesting question for the presenter.\n\nConversation history: {json.dumps(agent.conversation_history)}"
            
            chat_response = mistral_client.chat(
                model="mistral-small-latest",
                messages=[ChatMessage(role="user", content=prompt)],
            )
            
            questions.append({
                "agent_id": agent.id,
                "question": chat_response.messages[0].content
            })
        
        # Randomly select 5 questions
        selected_questions = random.sample(questions, min(5, len(questions)))
        return {"questions": selected_questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. Handle direct agent-presenter conversation
@app.post("/api/agent-conversation")
async def agent_conversation(data: Dict):
    try:
        agent_id = data.get("agent_id")
        presenter_response = data.get("presenter_response", "")
        emotion_data = data.get("emotion_data", {})
        
        agent = next((a for a in agents if a.id == agent_id), None)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update agent's context with presenter's response and emotion
        agent.conversation_history.append({
            "text": presenter_response,
            "emotion": emotion_data
        })
        
        # Generate agent's response
        prompt = f"{agent.personality}\n\nConversation history: {json.dumps(agent.conversation_history)}\n\nBased on the presenter's response and emotional state, provide a follow-up response or indicate if you're satisfied with the answer."
        
        chat_response = mistral_client.chat(
            model="mistral-small-latest",
            messages=[ChatMessage(role="user", content=prompt)],
        )
        
        response = chat_response.messages[0].content
        is_satisfied = "satisfied" in response.lower() or "thank you" in response.lower()
        
        return {
            "response": response,
            "is_satisfied": is_satisfied
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 8. Text-to-Speech endpoint (using Hume's EVI)
@app.post("/api/text-to-speech")
async def text_to_speech(data: Dict):
    try:
        text = data.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
            
        # Configure Hume for text-to-speech
        config = LanguageConfig(text_to_speech=True)
        job = await hume_client.submit_text(text, [config])
        
        results = []
        async for result in job.stream():
            results.append(result)
        
        # Extract audio data
        audio_data = results[0]["language"]["predictions"][0]["audio"]
        return {"audio_data": audio_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))