from typing import List, Dict
from datetime import datetime, timedelta

def rank(places: List[Dict], intent: str, scene_tags: List[str]) -> List[Dict]:
    """
    Rank places based on distance, ratings, scene bias, and other factors.
    
    Args:
        places: List of place dictionaries from places_api.py
        intent: Intent from intent.py (e.g., "quiet_study")
        scene_tags: Scene tags from scene_analyzer.py (e.g., ["day", "indoors"])
        
    Returns:
        List of ranked places with scores and human-readable reasons
        
    Example:
        rank(places, "quiet_study", ["day", "indoors"]) -> [{"name": "Blue Bottle", "score": 8.2, "reason": "Close (420m) • open now • 4.5★"}]
    """
    if not places:
        return []
    
    # Score each place
    for place in places:
        place["_score"] = calculate_score(place, intent, scene_tags)
        place["_reason"] = generate_reason(place, scene_tags)
    
    # Sort by score (highest first)
    ranked_places = sorted(places, key=lambda x: x["_score"], reverse=True)
    
    # Remove internal scoring fields and return top 3
    for place in ranked_places[:3]:
        place.pop("_score", None)
        place.pop("_reason", None)
    
    return ranked_places[:3]

def calculate_score(place: Dict, intent: str, scene_tags: List[str]) -> float:
    """
    Calculate a score for a place based on multiple factors.
    
    Scoring components:
    - Distance: Closer places get higher scores
    - Open now: Currently open places get bonus
    - Rating: Higher-rated places get bonus
    - Scene bias: Places matching desired scene get bonus
    - Closing soon: Places closing within 1 hour get warning
    """
    score = 0.0
    
    # Distance scoring (0-2 points, closer is better)
    distance_m = place.get("distance_m", 9999)
    if distance_m <= 1000:
        score += (1000 - distance_m) / 500.0  # 0-2 points
    else:
        score += 0.1  # Small bonus for very far places
    
    # Open now bonus (+2 points)
    if place.get("open_now", False):
        score += 2.0
    
    # Rating bonus
    rating = place.get("rating")
    if rating:
        if rating >= 4.3:
            score += 0.5
        elif rating >= 4.0:
            score += 0.25
    
    # Scene bias (matching desired scene gets bonus)
    score += calculate_scene_bias(place, scene_tags)
    
    # Closing soon warning (negative score for places closing within 1 hour)
    if is_closing_soon(place):
        score -= 0.5  # Small penalty, but still show the place
    
    return score

def calculate_scene_bias(place: Dict, scene_tags: List[str]) -> float:
    """
    Calculate scene bias based on how well the place matches desired scene.
    
    Scene bias rules:
    - "night" + bar/night_club = +0.6
    - "outdoors" + park = +0.6  
    - "indoors" + library/cafe = +0.6
    - "day" + outdoor activities = +0.6
    """
    bias = 0.0
    place_type = place.get("type", "")
    
    # Night scene bias
    if "night" in scene_tags and place_type in ["bar", "night_club"]:
        bias += 0.6
    
    # Outdoor scene bias
    if "outdoors" in scene_tags and place_type in ["park", "cafe"]:
        bias += 0.6
    
    # Indoor scene bias
    if "indoors" in scene_tags and place_type in ["library", "cafe"]:
        bias += 0.6
    
    # Day scene bias
    if "day" in scene_tags and place_type in ["park", "cafe"]:
        bias += 0.6
    
    return bias

def is_closing_soon(place: Dict) -> bool:
    """
    Check if a place is closing within 1 hour.
    This is a simplified version - in reality, you'd parse opening hours.
    """
    # For now, we'll assume places are open for a while
    # In a real implementation, you'd parse Google's opening_hours data
    return False

def generate_reason(place: Dict, scene_tags: List[str]) -> str:
    """
    Generate a human-readable reason for why this place is recommended.
    
    Examples:
    - "Close (420m) • open now • 4.5★"
    - "Close (200m) • 4.2★ • matches your vibe"
    - "Close (800m) • open now • 4.8★ • closing soon"
    """
    reasons = []
    
    # Distance
    distance_m = place.get("distance_m", 9999)
    if distance_m < 1000:
        reasons.append(f"Close ({distance_m}m)")
    else:
        reasons.append(f"{distance_m}m away")
    
    # Open now
    if place.get("open_now", False):
        reasons.append("open now")
    
    # Rating
    rating = place.get("rating")
    if rating:
        reasons.append(f"{rating}★")
    
    # Scene match
    if matches_scene(place, scene_tags):
        reasons.append("matches your vibe")
    
    # Closing soon
    if is_closing_soon(place):
        reasons.append("closing soon")
    
    return " • ".join(reasons)

def matches_scene(place: Dict, scene_tags: List[str]) -> bool:
    """
    Check if a place matches the desired scene.
    """
    place_type = place.get("type", "")
    
    # Night scene match
    if "night" in scene_tags and place_type in ["bar", "night_club"]:
        return True
    
    # Outdoor scene match
    if "outdoors" in scene_tags and place_type in ["park", "cafe"]:
        return True
    
    # Indoor scene match
    if "indoors" in scene_tags and place_type in ["library", "cafe"]:
        return True
    
    # Day scene match
    if "day" in scene_tags and place_type in ["park", "cafe"]:
        return True
    
    return False
