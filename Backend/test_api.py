import requests
import json
import time
import os

# Toggle between local and production
USE_LOCAL = False  # Set to False to test production

# Base URLs
LOCAL_URL = "http://localhost:3000"
PROD_URL = "https://hackathonbackend-7e7mcr2dg-saqib-rezas-projects.vercel.app"  # Updated to latest deployment

# Base URL for the API
BASE_URL = LOCAL_URL if USE_LOCAL else PROD_URL

print(f"Testing against: {BASE_URL}")

def test_transcribe():
    """
    Test audio transcription API
    Input: Audio file (WAV, MP3, M4A)
    Output: JSON with transcribed text
    """
    url = f"{BASE_URL}/api/transcribe"
    file_path = "(Audio) Martin Luther King - I Have A Dream Speech - August 28, 1963 (Full Speech).m4a"
    
    try:
        with open(file_path, 'rb') as audio_file:
            files = {
                'file': ('mlk_speech.m4a', audio_file, 'audio/x-m4a')
            }
            print("\nTesting transcription API...")
            response = requests.post(url, files=files)
            print_response(response)
            return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        return None

def test_audio_emotion():
    """
    Test audio emotion analysis API
    Input: Audio file (WAV, MP3, M4A)
    Output: JSON with emotion scores (joy, sadness, anger, etc.)
    """
    url = f"{BASE_URL}/api/analyze-audio-emotion"
    file_path = "(Audio) Martin Luther King - I Have A Dream Speech - August 28, 1963 (Full Speech).m4a"
    
    try:
        with open(file_path, 'rb') as audio_file:
            files = {
                'file': ('mlk_speech.m4a', audio_file, 'audio/x-m4a')
            }
            print("\nTesting audio emotion analysis API...")
            response = requests.post(url, files=files)
            print_response(response)
            return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Audio emotion analysis error: {str(e)}")
        return None

def test_video_emotion():
    """
    Test video emotion analysis API
    Input: Video file (MP4, MOV)
    Output: JSON with facial emotion predictions
    """
    url = f"{BASE_URL}/api/analyze-video-emotion"
    # Replace with path to your test video file
    file_path = "Cut Down I Have a Dream for Testing - Made with Clipchamp (1).mp4"  
    
    try:
        with open(file_path, 'rb') as video_file:
            files = {
                'file': ('test_video.mp4', video_file, 'video/mp4')
            }
            print("\nTesting video emotion analysis API...")
            response = requests.post(url, files=files)
            print_response(response)
    except FileNotFoundError:
        print("Video emotion test skipped: No test video file found")
    except Exception as e:
        print(f"Video emotion analysis error: {str(e)}")

def test_create_agents():
    """
    Test agent creation API
    Input: None
    Output: JSON array of 15 agents with random personalities
    """
    url = f"{BASE_URL}/api/create-agents"
    
    try:
        print("\nTesting agent creation API...")
        response = requests.post(url)
        print_response(response)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Agent creation error: {str(e)}")
        return None

def test_update_agents(transcription=None, emotion_data=None):
    """
    Test agent update API
    Input: JSON with emotion_data and transcribed_text
    Output: JSON with agent responses
    """
    url = f"{BASE_URL}/api/update-agents"
    
    # Default test data if none provided
    data = {
        "emotion_data": emotion_data or {
            "joy": 0.8,
            "confidence": 0.7,
            "enthusiasm": 0.6
        },
        "transcribed_text": transcription or "This is a test presentation about artificial intelligence."
    }
    
    try:
        print("\nTesting agent update API...")
        response = requests.post(url, json=data)
        print_response(response)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Agent update error: {str(e)}")
        return None

def test_generate_questions():
    """
    Test question generation API
    Input: None (uses existing agents' conversation history)
    Output: JSON with 5 randomly selected questions
    """
    url = f"{BASE_URL}/api/generate-questions"
    
    try:
        print("\nTesting question generation API...")
        response = requests.post(url)
        print_response(response)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Question generation error: {str(e)}")
        return None

def test_agent_conversation(agent_id="agent_0"):
    """
    Test agent conversation API
    Input: JSON with agent_id, presenter_response, and emotion_data
    Output: JSON with agent's response and satisfaction status
    """
    url = f"{BASE_URL}/api/agent-conversation"
    
    data = {
        "agent_id": agent_id,
        "presenter_response": "That's an interesting question. AI ethics is indeed a crucial topic.",
        "emotion_data": {
            "confidence": 0.8,
            "enthusiasm": 0.7
        }
    }
    
    try:
        print("\nTesting agent conversation API...")
        response = requests.post(url, json=data)
        print_response(response)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Agent conversation error: {str(e)}")
        return None

def test_text_to_speech():
    """
    Test text-to-speech API
    Input: JSON with text to convert
    Output: JSON with audio data
    """
    url = f"{BASE_URL}/api/text-to-speech"
    
    data = {
        "text": "Hello, this is a test of the text-to-speech system."
    }
    
    try:
        print("\nTesting text-to-speech API...")
        response = requests.post(url, json=data)
        print_response(response)
        
        # If successful, save the audio file
        if response.status_code == 200:
            audio_data = response.json().get("audio_data")
            if audio_data:
                with open("test_output.wav", "wb") as f:
                    f.write(bytes(audio_data))
                print("Audio saved as 'test_output.wav'")
    except Exception as e:
        print(f"Text-to-speech error: {str(e)}")

def print_response(response):
    """Helper function to print API responses with detailed debugging"""
    print(f"\nStatus Code: {response.status_code}")
    print("Headers:", json.dumps(dict(response.headers), indent=2))
    try:
        print("Response:", json.dumps(response.json(), indent=2))
    except:
        print("Raw Response:", response.text)
        if response.status_code == 401:
            print("\nDebugging 401 Error:")
            print("1. Verify API is receiving environment variables:")
            print("2. Check request headers:", json.dumps(dict(response.request.headers), indent=2))
            print("3. Full URL called:", response.request.url)

def run_all_tests():
    """Run all API tests in sequence"""
    print("Starting API tests...")
    
    # Create agents first as other tests depend on them
    agents = test_create_agents()
    
    # Run transcription and emotion analysis
    transcription = test_transcribe()
    emotion_data = test_audio_emotion()
    test_video_emotion()
    
    # Use results from previous tests if available
    if transcription and emotion_data:
        test_update_agents(
            transcription=transcription.get("transcription"),
            emotion_data=emotion_data.get("emotions")
        )
    else:
        test_update_agents()
    
    # Generate and handle questions
    questions = test_generate_questions()
    if questions and questions.get("questions"):
        first_agent = questions["questions"][0]["agent_id"]
        test_agent_conversation(first_agent)
    else:
        test_agent_conversation()
    
    # Test text-to-speech
    test_text_to_speech()
    
    print("\nAPI testing completed!")

if __name__ == "__main__":
    print("\nTesting single endpoint first for debugging...")
    test_create_agents()  # This endpoint doesn't require file upload, good for initial testing
    
    if input("\nContinue with file-based tests? (y/n): ").lower() == 'y':
        test_transcribe()
        test_audio_emotion()
    
    #run_all_tests() 