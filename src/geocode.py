"""
Geocoding service integration module.
Handles interaction with geocoding APIs (Google Maps, OSM, etc.)
"""
import time
from typing import Optional, Dict, List, Tuple
import googlemaps
from datetime import datetime

from . import config


class GeocodingService:
    """Wrapper for geocoding API interactions."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize geocoding service.
        
        Args:
            api_key: Google Maps API key (uses config if not provided)
        """
        self.api_key = api_key or config.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            raise ValueError("Google Maps API key not configured")
        
        self.client = googlemaps.Client(key=self.api_key)
        self.call_count = 0
        self.last_call_time = None
    
    def geocode_company(
        self, 
        company: str, 
        site_hint: str = None,
        country_hint: str = None
    ) -> Optional[List[Dict]]:
        """
        Geocode a company name with optional location hints.
        
        Args:
            company: Company name
            site_hint: Optional location hint (e.g., "Pune, India")
            country_hint: Optional ISO-2 country code (e.g., "IN")
        
        Returns:
            List of geocoding results, or None if no results
        """
        # Construct query
        query = company.strip()
        if site_hint:
            query = f"{query}, {site_hint}"
        
        # Build API parameters
        params = {}
        if country_hint:
            # Use components filter for country bias
            params['components'] = {'country': country_hint}
        
        try:
            # Make API call
            self._track_api_call()
            results = self.client.geocode(query, **params)
            
            if not results:
                return None
            
            return results
        
        except googlemaps.exceptions.ApiError as e:
            print(f"Geocoding API error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error during geocoding: {e}")
            return None
    
    def parse_geocode_result(self, result: Dict) -> Dict:
        """
        Parse geocoding result into standardized address components.
        
        Args:
            result: Raw geocoding result from API
        
        Returns:
            Dict with parsed address components
        """
        # Extract address components
        components = {}
        for component in result.get('address_components', []):
            types = component.get('types', [])
            long_name = component.get('long_name', '')
            short_name = component.get('short_name', '')
            
            # Map component types to our fields
            if 'street_number' in types:
                components['street_number'] = long_name
            elif 'route' in types:
                components['route'] = long_name
            elif 'subpremise' in types:
                components['subpremise'] = long_name
            elif 'premise' in types:
                components['premise'] = long_name
            elif 'locality' in types:
                components['city'] = long_name
            elif 'postal_town' in types and 'city' not in components:
                components['city'] = long_name
            elif 'administrative_area_level_2' in types and 'city' not in components:
                components['city'] = long_name
            elif 'administrative_area_level_1' in types:
                components['state_region'] = long_name
            elif 'country' in types:
                components['country'] = short_name  # ISO-2 code
                components['country_long'] = long_name
            elif 'postal_code' in types:
                components['postal_code'] = long_name
        
        # Build street address
        street_parts = []
        if 'street_number' in components:
            street_parts.append(components['street_number'])
        if 'route' in components:
            street_parts.append(components['route'])
        if 'premise' in components:
            street_parts.insert(0, components['premise'])
        
        street_1 = ' '.join(street_parts) if street_parts else result.get('formatted_address', '').split(',')[0]
        street_2 = components.get('subpremise', '')
        
        # Extract location
        geometry = result.get('geometry', {})
        location = geometry.get('location', {})
        
        # Calculate confidence
        confidence = self._calculate_confidence(result)
        
        return {
            'street_1': street_1,
            'street_2': street_2,
            'city': components.get('city', ''),
            'state_region': components.get('state_region', ''),
            'postal_code': components.get('postal_code', ''),
            'country': components.get('country', ''),
            'country_long': components.get('country_long', ''),
            'lat': location.get('lat'),
            'lng': location.get('lng'),
            'formatted_address': result.get('formatted_address', ''),
            'place_id': result.get('place_id', ''),
            'confidence': confidence,
            'result_types': result.get('types', []),
        }
    
    def _calculate_confidence(self, result: Dict) -> float:
        """
        Calculate confidence score for geocoding result.
        
        Args:
            result: Geocoding result
        
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 1.0
        
        # Penalize partial matches
        if result.get('partial_match', False):
            confidence -= 0.20
        
        # Prefer specific result types
        result_types = result.get('types', [])
        preferred_types = ['street_address', 'premise', 'establishment', 'point_of_interest']
        generic_types = ['locality', 'administrative_area_level_1', 'country']
        
        has_preferred = any(t in result_types for t in preferred_types)
        has_generic = any(t in result_types for t in generic_types)
        
        if not has_preferred and has_generic:
            confidence -= 0.25
        
        # Check geometry location type
        geometry = result.get('geometry', {})
        location_type = geometry.get('location_type', '')
        
        if location_type == 'APPROXIMATE':
            confidence -= 0.15
        elif location_type == 'GEOMETRIC_CENTER':
            confidence -= 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _track_api_call(self):
        """Track API call for rate limiting."""
        self.call_count += 1
        self.last_call_time = datetime.now()
        
        # Warn if approaching limits
        if self.call_count >= config.WARNING_THRESHOLD:
            print(f"⚠️  Warning: {self.call_count} API calls made today (limit: {config.MAX_API_CALLS_PER_DAY})")
        
        # Enforce hard limit
        if self.call_count >= config.MAX_API_CALLS_PER_DAY:
            raise Exception(f"Daily API call limit reached ({config.MAX_API_CALLS_PER_DAY})")
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Reverse geocode coordinates to address (for validation).
        
        Args:
            lat: Latitude
            lng: Longitude
        
        Returns:
            Parsed address or None
        """
        try:
            self._track_api_call()
            results = self.client.reverse_geocode((lat, lng))
            
            if results:
                return self.parse_geocode_result(results[0])
            return None
        
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None


def extract_country_hint(site_hint: str) -> Optional[str]:
    """
    Extract country code from site hint.
    
    Args:
        site_hint: Location hint (e.g., "Pune, India" or "Pune, IN")
    
    Returns:
        ISO-2 country code or None
    """
    if not site_hint:
        return None
    
    # Common country mappings
    country_map = {
        'INDIA': 'IN',
        'IN': 'IN',
        'USA': 'US',
        'US': 'US',
        'UNITED STATES': 'US',
        'UK': 'GB',
        'UNITED KINGDOM': 'GB',
        'CANADA': 'CA',
        'CA': 'CA',
        'AUSTRALIA': 'AU',
        'AU': 'AU',
        'GERMANY': 'DE',
        'DE': 'DE',
        'FRANCE': 'FR',
        'FR': 'FR',
        'JAPAN': 'JP',
        'JP': 'JP',
        'CHINA': 'CN',
        'CN': 'CN',
    }
    
    # Check last part of hint (usually country)
    parts = [p.strip().upper() for p in site_hint.split(',')]
    if parts:
        last_part = parts[-1]
        return country_map.get(last_part)
    
    return None


if __name__ == "__main__":
    # Test geocoding service
    print("Geocoding Service Test")
    print("=" * 60)
    
    # Note: This requires valid API key in .env
    try:
        service = GeocodingService()
        
        # Test query
        results = service.geocode_company("Tata Consultancy Services", "Pune, India")
        
        if results:
            print(f"Found {len(results)} results")
            parsed = service.parse_geocode_result(results[0])
            print("\nParsed result:")
            for key, value in parsed.items():
                print(f"  {key}: {value}")
        else:
            print("No results found")
    
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set GOOGLE_MAPS_API_KEY in .env file")
