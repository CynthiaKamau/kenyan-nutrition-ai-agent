import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class AgentFeedback:
    """Feedback data structure for agent performance"""
    agent_name: str
    session_id: str
    user_input: Dict[str, Any]
    agent_output: Dict[str, Any]
    user_rating: Optional[int] = None  # 1-5 scale
    user_comments: Optional[str] = None
    accuracy_metrics: Optional[Dict[str, float]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class FeedbackCollector:
    """Collects and stores feedback for agent performance analysis"""
    
    def __init__(self, feedback_dir: str = "feedback_data"):
        self.feedback_dir = feedback_dir
        self.logger = logging.getLogger(__name__)
        os.makedirs(feedback_dir, exist_ok=True)
    
    def collect_user_feedback(self, agent_name: str, session_id: str, 
                             user_input: Dict[str, Any], agent_output: Dict[str, Any]) -> AgentFeedback:
        """Collect feedback from user about agent performance"""
        
        print(f"\n📊 FEEDBACK FOR {agent_name.upper().replace('-', ' ')}")
        print("Your feedback helps improve our AI recommendations!")
        
        try:
            # Rating
            while True:
                rating_input = input("Rate the accuracy of recommendations (1-5, 5=excellent): ")
                try:
                    rating = int(rating_input)
                    if 1 <= rating <= 5:
                        break
                    else:
                        print("Please enter a number between 1 and 5")
                except ValueError:
                    print("Please enter a valid number")
            
            # Comments
            comments = input("Additional comments (optional): ").strip()
            if not comments:
                comments = None
            
            feedback = AgentFeedback(
                agent_name=agent_name,
                session_id=session_id,
                user_input=user_input,
                agent_output=agent_output,
                user_rating=rating,
                user_comments=comments
            )
            
            self.save_feedback(feedback)
            return feedback
            
        except KeyboardInterrupt:
            print("\nFeedback collection cancelled")
            return None
    
    def save_feedback(self, feedback: AgentFeedback):
        """Save feedback to file"""
        filename = f"{feedback.agent_name}_{feedback.session_id}_{feedback.timestamp.replace(':', '-')}.json"
        filepath = os.path.join(self.feedback_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(feedback), f, indent=2)
            self.logger.info(f"Feedback saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving feedback: {e}")
    
    def calculate_agent_metrics(self, agent_name: str) -> Dict[str, float]:
        """Calculate performance metrics for an agent"""
        feedback_files = [f for f in os.listdir(self.feedback_dir) if f.startswith(agent_name)]
        
        if not feedback_files:
            return {"average_rating": 0.0, "total_sessions": 0}
        
        ratings = []
        for filename in feedback_files:
            try:
                with open(os.path.join(self.feedback_dir, filename), 'r') as f:
                    feedback_data = json.load(f)
                    if feedback_data.get('user_rating'):
                        ratings.append(feedback_data['user_rating'])
            except Exception as e:
                self.logger.error(f"Error reading feedback file {filename}: {e}")
        
        if ratings:
            return {
                "average_rating": sum(ratings) / len(ratings),
                "total_sessions": len(ratings),
                "rating_distribution": {str(i): ratings.count(i) for i in range(1, 6)}
            }
        else:
            return {"average_rating": 0.0, "total_sessions": 0}
