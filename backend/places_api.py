import json
import os
import requests
import math
from datetime import datetime
from typing import List, Dict

# Load vibe_mapper.json to get place types for each intent
with open("vibe_mapper.json", "r") as f:
    VIBE_MAPPER = json.load(f)

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    
    Args:
        lat1, lng1: First point coordinates (latitude, longitude)
        lat2, lng2: Second point coordinates (latitude, longitude)
        
    Returns:
        Distance in meters
        
    Example:
        haversine(37.7749, -122.4194, 37.7849, -122.4094) -> ~1000 (meters)
    """
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in meters
    earth_radius = 6371000
    
    return earth_radius * c

def search_nearby(intent: str, lat: float, lng: float, radius: int = 1500) -> List[Dict]:
    """
    Search for nearby places using Google Places API based on intent.
    
    Args:
        intent: Intent from vibe_mapper.json (e.g., "quiet_study")
        lat: User's latitude
        lng: User's longitude  
        radius: Search radius in meters (default: 1500)
        
    Returns:
        List of place dictionaries with name, place_id, type, distance_m, etc.
        
    Example:
        search_nearby("quiet_study", 37.7749, -122.4194) -> [{"name": "Blue Bottle Coffee", ...}]
    """
    # Get Google Maps API key from environment
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Warning: GOOGLE_MAPS_API_KEY not found in environment")
        return []
    
    # Get place types for this intent
    if intent not in VIBE_MAPPER:
        return []
    
    place_types = VIBE_MAPPER[intent]["types"]  # Use all types for this intent
    all_places = []
    
    # First pass: Search for each place type (max 3 per type for variety)
    for place_type in place_types:
        try:
            # Build Google Places API request
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "key": api_key,
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": place_type,
                "opennow": True  # Only return places that are currently open
            }
            
            # Make API request
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Check if API call was successful
            if data.get("status") != "OK":
                print(f"Google Places API error: {data.get('status')}")
                continue
            
            # Process each place result (limit to 3 per type for variety)
            type_count = 0
            for place in data.get("results", []):
                if type_count >= 3:  # Max 3 places per type
                    break
                    
                place_data = {
                    "name": place.get("name", "Unknown"),
                    "place_id": place.get("place_id", ""),
                    "type": place_type,  # Which type matched
                    "rating": place.get("rating"),
                    "user_ratings_total": place.get("user_ratings_total", 0),
                    "open_now": place.get("opening_hours", {}).get("open_now", False),
                    "vicinity": place.get("vicinity", ""),
                    "geometry": place.get("geometry", {}),
                }
                
                # Calculate distance from user
                if "location" in place_data["geometry"]:
                    place_lat = place_data["geometry"]["location"]["lat"]
                    place_lng = place_data["geometry"]["location"]["lng"]
                    place_data["distance_m"] = int(haversine(lat, lng, place_lat, place_lng))
                else:
                    place_data["distance_m"] = 9999  # Fallback for missing coordinates
                
                all_places.append(place_data)
                type_count += 1
                
        except Exception as e:
            print(f"Error searching for {place_type}: {e}")
            continue
    
    # Second pass: If we don't have 6 places, fill up from remaining results
    if len(all_places) < 6:
        for place_type in place_types:
            if len(all_places) >= 6:
                break
                
            try:
                # Build Google Places API request
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "key": api_key,
                    "location": f"{lat},{lng}",
                    "radius": radius,
                    "type": place_type,
                    "opennow": True  # Only return places that are currently open
                }
                
                # Make API request
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                # Check if API call was successful
                if data.get("status") != "OK":
                    continue
                
                # Process remaining places (skip first 3, get more)
                type_count = 0
                for place in data.get("results", []):
                    if len(all_places) >= 6:
                        break
                    if type_count < 3:  # Skip first 3 (already processed)
                        type_count += 1
                        continue
                    
                    place_data = {
                        "name": place.get("name", "Unknown"),
                        "place_id": place.get("place_id", ""),
                        "type": place_type,  # Which type matched
                        "rating": place.get("rating"),
                        "user_ratings_total": place.get("user_ratings_total", 0),
                        "open_now": place.get("opening_hours", {}).get("open_now", False),
                        "vicinity": place.get("vicinity", ""),
                        "geometry": place.get("geometry", {}),
                    }
                    
                    # Calculate distance from user
                    if "location" in place_data["geometry"]:
                        place_lat = place_data["geometry"]["location"]["lat"]
                        place_lng = place_data["geometry"]["location"]["lng"]
                        place_data["distance_m"] = int(haversine(lat, lng, place_lat, place_lng))
                    else:
                        place_data["distance_m"] = 9999  # Fallback for missing coordinates
                    
                    all_places.append(place_data)
                    type_count += 1
                    
            except Exception as e:
                print(f"Error in second pass for {place_type}: {e}")
                continue
    
    # Remove duplicates by place_id and limit results
    seen_ids = set()
    unique_places = []
    for place in all_places:
        if place["place_id"] not in seen_ids:
            seen_ids.add(place["place_id"])
            unique_places.append(place)
            if len(unique_places) >= 6:  # Limit to 6 candidates
                break
    
    return unique_places
