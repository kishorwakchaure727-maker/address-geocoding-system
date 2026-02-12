"""
Fuzzy matching and deduplication logic.
"""
from typing import List, Dict, Optional, Tuple
from rapidfuzz import fuzz, process


def find_best_match(
    query: str,
    candidates: List[Dict],
    key_field: str = 'company_normalized',
    threshold: int = 80
) -> Optional[Tuple[Dict, float]]:
    """
    Find best fuzzy match from candidates.
    
    Args:
        query: Query string (normalized company name)
        candidates: List of candidate records
        key_field: Field name to match against
        threshold: Minimum similarity score (0-100)
    
    Returns:
        Tuple of (best_match, score) or None
    """
    if not candidates:
        return None
    
    # Extract strings to match
    choices = [(rec, rec.get(key_field, '')) for rec in candidates]
    
    # Find best match
    result = process.extractOne(
        query,
        [choice[1] for choice in choices],
        scorer=fuzz.token_set_ratio
    )
    
    if result:
        match_str, score, idx = result
        if score >= threshold:
            return choices[idx][0], score
    
    return None


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings.
    
    Args:
        str1: First string
        str2: Second string
    
    Returns:
        Similarity score (0-100)
    """
    return fuzz.token_set_ratio(str1, str2)


def deduplicate_results(
    results: List[Dict],
    key_field: str =' company_normalized',
    threshold: int = 95
) -> List[Dict]:
    """
    Remove duplicate/very similar results.
    
    Args:
        results: List of records
        key_field: Field to use for deduplication
        threshold: Similarity threshold for considering duplicates
    
    Returns:
        Deduplicated list
    """
    if not results:
        return []
    
    unique = []
    seen = []
    
    for record in results:
        value = record.get(key_field, '')
        if not value:
            continue
        
        # Check if similar to any seen value
        is_duplicate = False
        for seen_value in seen:
            if fuzz.ratio(value, seen_value) >= threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique.append(record)
            seen.append(value)
    
    return unique


def rank_by_proximity(
    results: List[Dict],
    target_lat: float,
    target_lng: float
) -> List[Dict]:
    """
    Rank results by proximity to target coordinates.
    
    Args:
        results: List of records with lat/lng
        target_lat: Target latitude
        target_lng: Target longitude
    
    Returns:
        Sorted list (closest first)
    """
    from math import radians, cos, sin, asin, sqrt
    
    def haversine(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km."""
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km
    
    # Calculate distances
    for result in results:
        try:
            lat = float(result.get('lat', 0))
            lng = float(result.get('lng', 0))
            dist = haversine(target_lat, target_lng, lat, lng)
            result['_distance_km'] = dist
        except (ValueError, TypeError):
            result['_distance_km'] = float('inf')
    
    # Sort by distance
    return sorted(results, key=lambda x: x.get('_distance_km', float('inf')))


if __name__ == "__main__":
    # Test matching
    print("Fuzzy Matching Test")
    print("=" * 60)
    
    candidates = [
        {'company_normalized': 'TATA CONSULTANCY SERVICES', 'city': 'Pune'},
        {'company_normalized': 'TATA MOTORS', 'city': 'Mumbai'},
        {'company_normalized': 'INFOSYS LIMITED', 'city': 'Bangalore'},
    ]
    
    queries = [
        'TATA CONSULTANCY',
        'TCS',
        'INFOSYS',
        'WIPRO',
    ]
    
    for query in queries:
        match = find_best_match(query, candidates)
        if match:
            record, score = match
            print(f"{query:25} → {record['company_normalized']} (score: {score:.1f})")
        else:
            print(f"{query:25} → No match found")
