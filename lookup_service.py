"""
Main lookup service - orchestrates all components.
"""
from typing import Optional, Dict, Tuple
from datetime import datetime

from src import config
from src.normalize import normalize_company
from src.geocode import GeocodingService, extract_country_hint
from src.storage import get_cache, SheetsStorage
from src.matching import find_best_match
from src.validators import validate_address_record, suggest_manual_review


class AddressLookupService:
    """Main service for address lookups."""
    
    def __init__(self):
        """Initialize the lookup service."""
        self.geocoder = None
        self.storage = None
        self.cache = get_cache()
    
    def _init_geocoder(self):
        """Lazy initialize geocoder."""
        if self.geocoder is None:
            self.geocoder = GeocodingService()
    
    def _init_storage(self):
        """Lazy initialize storage."""
        if self.storage is None:
            self.storage = SheetsStorage()
    
    def lookup(
        self,
        company: str,
        site_hint: str = None
    ) -> Tuple[Optional[Dict], str]:
        """
        Look up company address with automatic caching and geocoding.
        
        Args:
            company: Company name (raw input)
            site_hint: Optional location hint (e.g., "Pune, India")
        
        Returns:
            Tuple of (address_record, source)
            source can be: 'cache', 'storage', 'geocoded', 'not_found'
        """
        # Normalize company name
        company_normalized = normalize_company(company)
        
        if not company_normalized:
            return None, 'invalid_input'
        
        # Extract country hint for filtering
        country_hint = extract_country_hint(site_hint) if site_hint else None
        city_hint = None
        if site_hint and ',' in site_hint:
            city_hint = site_hint.split(',')[0].strip()
        
        # 1. Check cache first
        cached = self.cache.get(
            company_normalized,
            city=city_hint,
            country=country_hint
        )
        if cached:
            print(f"✓ Cache hit for {company_normalized}")
            return cached, 'cache'
        
        # 2. Check storage (Google Sheets)
        self._init_storage()
        
        # Try exact match
        stored = self.storage.find_by_exact_match(
            company_normalized,
            city=city_hint,
            country=country_hint
        )
        
        if stored:
            print(f"✓ Storage hit (exact match) for {company_normalized}")
            # Update cache
            self.cache.set(stored, company_normalized, city_hint, country_hint)
            return stored, 'storage'
        
        # Try fuzzy match
        fuzzy_results = self.storage.search_fuzzy(
            company_normalized,
            country=country_hint
        )
        
        if fuzzy_results:
            best_match, score = find_best_match(
                company_normalized,
                fuzzy_results,
                threshold=85
            )
            
            if best_match:
                print(f"✓ Storage hit (fuzzy match, score: {score:.1f}) for {company_normalized}")
                self.cache.set(best_match, company_normalized, city_hint, country_hint)
                return best_match, 'storage_fuzzy'
        
        # 3. not in storage - geocode it
        self._init_geocoder()
        
        print(f"⟳ Geocoding {company} {site_hint or ''}")
        
        results = self.geocoder.geocode_company(
            company,
            site_hint=site_hint,
            country_hint=country_hint
        )
        
        if not results or len(results) == 0:
            print(f"✗ No geocoding results for {company}")
            return None, 'not_found'
        
        # Parse top result
        parsed = self.geocoder.parse_geocode_result(results[0])
        
        # Build record
        record = {
            'company_raw': company,
            'company_normalized': company_normalized,
            'site_hint': site_hint or '',
            'street_1': parsed['street_1'],
            'street_2': parsed['street_2'],
            'city': parsed['city'],
            'state_region': parsed['state_region'],
            'postal_code': parsed['postal_code'],
            'country': parsed['country'],
            'lat': parsed['lat'],
            'lng': parsed['lng'],
            'source': 'google',
            'confidence': parsed['confidence'],
            'geocoder_place_id': parsed['place_id'],
            'qa_status': 'auto' if parsed['confidence'] >= config.CONFIDENCE_THRESHOLD else 'review',
            'notes': '',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }
        
        # Validate
        is_valid, errors = validate_address_record(record)
        if not is_valid:
            print(f"⚠️  Validation warnings: {', '.join(errors)}")
            record['qa_status'] = 'review'
            record['notes'] = 'Validation issues: ' + '; '.join(errors)
        
        # Store in Sheets
        success = self.storage.insert(record)
        
        if success:
            print(f"✓ Saved to storage (confidence: {parsed['confidence']:.2f})")
            # Update cache
            self.cache.set(record, company_normalized, city_hint, country_hint)
        else:
            print(f"✗ Failed to save to storage")
        
        return record, 'geocoded'
    
    def get_stats(self) -> Dict:
        """Get service statistics."""
        self._init_storage()
        
        storage_stats = self.storage.get_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'storage': storage_stats,
            'cache': cache_stats,
        }
    
    def get_review_queue(self) -> list:
        """Get records needing manual review."""
        self._init_storage()
        return self.storage.get_low_confidence_records()


# Global service instance
_service = None

def get_lookup_service() -> AddressLookupService:
    """Get global lookup service instance."""
    global _service
    if _service is None:
        _service = AddressLookupService()
    return _service


if __name__ == "__main__":
    # Test lookup service
    print("Address Lookup Service Test")
    print("=" * 60)
    
    service = AddressLookupService()
    
    #Test query
    test_queries = [
        ("Tata Consultancy Services", "Pune, India"),
        ("HDFC Bank", "Mumbai, India"),
    ]
    
    for company, site_hint in test_queries:
        print(f"\nLooking up: {company}, {site_hint}")
        record, source = service.lookup(company, site_hint)
        
        if record:
            print(f"  Source: {source}")
            print(f"  Address: {record.get('formatted_address', record.get('street_1', ''))}")
            print(f"  City: {record.get('city')}, {record.get('country')}")
            print(f"  Confidence: {record.get('confidence')}")
        else:
            print(f"  Not found ({source})")
