import os
from datetime import datetime
from langchain_core.tools import tool
from julius.core.config import DATA_DIR

# Predefined System Design interview scenarios
SCENARIOS = {
    "rate_limiter": (
        "Topic: Design a Rate Limiter\n"
        "Requirements:\n"
        "1. Limit requests by IP, User ID, or API Key.\n"
        "2. Support low latency (< 1ms overhead per request).\n"
        "3. Scalability: Handle 10M daily active users with high availability.\n"
        "4. Clarifying questions to ask: What algorithms should we consider (Token Bucket, Leaky Bucket, Sliding Window Log)? How do we distribute state in a cluster?"
    ),
    "url_shortener": (
        "Topic: Design a URL Shortener (e.g., TinyURL)\n"
        "Requirements:\n"
        "1. Generate a unique short alias for any given long URL.\n"
        "2. Fast redirection (< 10ms response time).\n"
        "3. Scale: 100M new short URLs per month. Highly read-heavy.\n"
        "4. Clarifying questions to ask: What is the URL expiration policy? How do we handle database replication and caching?"
    ),
    "video_streaming": (
        "Topic: Design a Video Streaming Service (e.g., Netflix/YouTube)\n"
        "Requirements:\n"
        "1. Upload and transcode videos in multiple resolutions.\n"
        "2. Low buffering, high quality global playback.\n"
        "3. Scale: 100M active daily users, petabytes of streaming data.\n"
        "4. Clarifying questions to ask: How do we design the CDN architecture? How is video chunking and metadata storage handled?"
    ),
    "chat_service": (
        "Topic: Design a Real-time Chat Service (e.g., WhatsApp/Slack)\n"
        "Requirements:\n"
        "1. Support 1-on-1 messaging and group chats.\n"
        "2. Real-time online/offline status, read receipts.\n"
        "3. Low latency delivery (< 100ms message delivery).\n"
        "4. Clarifying questions to ask: What connection protocol should we use (WebSockets, SSE, Long Polling)? How do we handle offline message sync?"
    ),
    "ride_hailing": (
        "Topic: Design a Ride Hailing System (e.g., Uber/Lyft)\n"
        "Requirements:\n"
        "1. Match riders with nearby drivers in real-time.\n"
        "2. Dynamic surge pricing based on demand/supply.\n"
        "3. Scale: 50K rides per minute globally.\n"
        "4. Clarifying questions to ask: How do we track driver geospatial coordinates (geohashes)? How do we handle matching queue consistency?"
    )
}

@tool
def get_system_design_scenario(topic: str) -> str:
    """
    Retrieves a structured system design interview scenario based on the topic.
    Available topics: 'rate_limiter', 'url_shortener', 'video_streaming', 'chat_service', 'ride_hailing'.
    Use this to load the prompt/requirements at the start of a mock interview.
    """
    topic_cleaned = topic.strip().lower().replace(" ", "_")
    
    # Fuzzy match basic topics
    for key in SCENARIOS:
        if key in topic_cleaned or topic_cleaned in key:
            return SCENARIOS[key]
            
    # Default message if no match found
    available_topics = ", ".join([f"'{k}'" for k in SCENARIOS.keys()])
    return (
        f"Topic '{topic}' was not found. Please choose one of the available topics: {available_topics}, "
        "or ask the candidate to define their own custom scenario."
    )

@tool
def save_evaluation(feedback_notes: str) -> str:
    """
    Saves candidate evaluation and feedback notes to a local file for future review.
    Always use this tool when the candidate finishes the interview mock session to persist notes.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    eval_file = os.path.join(DATA_DIR, "evaluations.txt")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"========================================\n"
        f"TIMESTAMP: {timestamp}\n"
        f"FEEDBACK & EVALUATION NOTES:\n"
        f"{feedback_notes.strip()}\n"
        f"========================================\n\n"
    )
    
    try:
        with open(eval_file, "a", encoding="utf-8") as f:
            f.write(entry)
        return "Evaluation successfully saved to data/evaluations.txt."
    except Exception as e:
        return f"Failed to save evaluation to file: {e}"
