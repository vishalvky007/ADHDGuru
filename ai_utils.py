import google.generativeai as genai
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import GOOGLE_API_KEY, MODEL_NAME
import json

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Flag to track if Gemini API is working
gemini_api_working = False

# Configure Google Generative AI
try:
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME)
        # Test the API with a simple query
        response = model.generate_content("Hello")
        if response:
            gemini_api_working = True
            print("Successfully connected to Google Generative AI API")
    else:
        print("Warning: GOOGLE_API_KEY not provided. Using fallback responses.")
except Exception as e:
    print(f"Error connecting to Google Generative AI API: {str(e)}")

def detect_tone(user_input):
    """Detect the tone/sentiment of the user input"""
    score = analyzer.polarity_scores(user_input)
    if score['compound'] >= 0.05:
        return "positive"
    elif score['compound'] <= -0.05:
        return "negative"
    else:
        return "neutral"

def classify_user(user_input):
    """Classify user type based on input content"""
    user_input = user_input.lower()
    if "parent" in user_input:
        return "Parent of an ADHD child"
    elif "teacher" in user_input or "educator" in user_input:
        return "Teacher/Educator working with ADHD students"
    elif "employer" in user_input:
        return "Employer managing an ADHD employee"
    elif "adhd" in user_input or "adult" in user_input:
        return "Adult with ADHD"
    else:
        return "General user (uncategorized)"

class MockResponse:
    """Mock response object for fallback when API is unavailable"""
    def __init__(self, text):
        self.text = text

class MockStreamingResponse:
    """Mock streaming response for fallback when API is unavailable"""
    def __init__(self, text):
        self.chunks = []
        # Split text into smaller chunks to simulate streaming
        words = text.split()
        current_chunk = ""
        for word in words:
            current_chunk += word + " "
            if len(current_chunk) > 10:  # Create chunk every ~10 chars
                self.chunks.append(current_chunk)
                current_chunk = ""
        if current_chunk:
            self.chunks.append(current_chunk)
        
        self.index = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.index < len(self.chunks):
            chunk = MockResponse(self.chunks[self.index])
            self.index += 1
            return chunk
        raise StopIteration

def get_fallback_response(message, user_category):
    """Generate fallback responses when Gemini API is unavailable"""
    responses = {
        "Adult with ADHD": [
            "As someone with ADHD, you might find it helpful to break tasks into smaller steps. What specific challenge are you facing today?",
            "Have you tried using timers or alarms to help manage time? Many adults with ADHD find external reminders helpful.",
            "Creating a structured routine can be beneficial for managing ADHD symptoms. Would you like some suggestions on how to establish one?"
        ],
        "Parent of an ADHD child": [
            "Parenting a child with ADHD comes with unique challenges. One strategy is to establish clear routines and expectations.",
            "Positive reinforcement can be very effective with ADHD children. Try to catch them doing well and provide immediate praise.",
            "Setting up a consistent homework environment might help your child focus better. Would you like some suggestions?"
        ],
        "Teacher/Educator working with ADHD students": [
            "Many educators find that providing written instructions alongside verbal ones helps ADHD students stay on track.",
            "Consider allowing movement breaks for students with ADHD. This can help them refocus and better engage with learning.",
            "Using visual timers in the classroom can help ADHD students manage their time better during assignments."
        ],
        "Employer managing an ADHD employee": [
            "Clear communication and written follow-ups after meetings can be very helpful for employees with ADHD.",
            "Consider offering a quieter workspace option if possible, as many with ADHD struggle with environmental distractions.",
            "Setting clear deadlines and breaking larger projects into smaller milestones can help ADHD employees manage their workload."
        ],
        "General user (uncategorized)": [
            "I'm here to help with ADHD-related questions. Could you tell me more about your specific situation?",
            "Organization and time management are common challenges with ADHD. Would you like some strategies for either of these areas?",
            "Medication is just one part of ADHD management. Behavioral strategies and environmental modifications can also be very effective."
        ]
    }
    
    # Get response based on user category
    category_responses = responses.get(user_category, responses["General user (uncategorized)"])
    
    # Use keywords in message to try to provide more relevant response
    lower_message = message.lower()
    for keyword, response_list in {
        "time": ["Time management can be challenging with ADHD. Have you tried using the Pomodoro technique?"],
        "focus": ["To improve focus, try minimizing distractions in your environment and breaking tasks into smaller chunks."],
        "medication": ["Medication can be helpful for many with ADHD, but it's important to work closely with your healthcare provider."],
        "sleep": ["Sleep difficulties are common with ADHD. Establishing a consistent bedtime routine may help."],
        "anxiety": ["ADHD and anxiety often occur together. Mindfulness techniques might help with both conditions."],
        "school": ["For school challenges, talking with teachers about accommodations can be very helpful."]
    }.items():
        if keyword in lower_message:
            return response_list[0]
    
    # Return a random response from the category if no keywords matched
    import random
    return random.choice(category_responses)

def get_ai_response(message, chat_history=[]):
    """Get a response from the AI model with streaming support"""
    # Prepare system prompt based on user category
    user_category = classify_user(message)
    
    if gemini_api_working:
        try:
            # Create a new chat session
            chat = model.start_chat(history=[])
            
            system_prompt = f"""
            You are an ADHD support chatbot with the personality of a warm, supportive counselor. 
            Your job is to provide clear, concise, and structured guidance to users based on their needs.

            User type: {user_category}

            - If they are an ADHD adult, offer self-management strategies.
            - If they are a parent, provide parenting tips.
            - If they are a teacher, suggest ADHD-friendly teaching techniques.
            - If they are an employer, recommend workplace accommodations.
            """
            
            # Add system prompt and chat history
            chat.send_message(system_prompt)
            for msg in chat_history:
                try:
                    chat.send_message(msg['content'])
                except Exception:
                    # Skip any problematic messages in history
                    continue
            
            # Get streaming response from the model
            return chat.send_message(message, stream=True)
        except Exception as e:
            print(f"Error getting AI response: {str(e)}")
            # If API call fails, use fallback
            fallback_response = get_fallback_response(message, user_category)
            return MockStreamingResponse(fallback_response)
    else:
        # API not working, use fallback
        fallback_response = get_fallback_response(message, user_category)
        return MockStreamingResponse(fallback_response)

def generate_title(content):
    """Generate a title for journal entry content"""
    if gemini_api_working:
        try:
            prompt = f"""
            Generate a concise, meaningful title (maximum 5 words) for this journal entry:
            {content}
            
            Return only the title, nothing else.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating title: {str(e)}")
            return "Journal Entry " + datetime.now().strftime("%Y-%m-%d")
    else:
        # Fallback title generation when API is unavailable
        from datetime import datetime
        import re
        
        # Simple title generation from content
        words = content.split()
        if len(words) >= 3:
            # Use first 3-5 significant words
            title_words = []
            for word in words:
                # Skip short words and common stop words
                if len(word) > 3 and word.lower() not in ['this', 'that', 'with', 'from', 'have', 'what', 'when', 'where', 'which']:
                    title_words.append(word)
                    if len(title_words) >= 5:
                        break
            
            if title_words:
                return " ".join(title_words)
        
        # Default to date-based title
        return "Journal Entry " + datetime.now().strftime("%Y-%m-%d") 