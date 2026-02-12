"""
Data validation and quality control functions.
"""
import re
from typing import Optional, Dict, List


# Postal code patterns by country
POSTAL_CODE_PATTERNS = {
    'IN': r'^\d{6}$',  # India: 6 digits
    'US': r'^\d{5}(-\d{4})?$',  # USA: 5 or 5+4 digits
    'GB': r'^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$',  # UK
    'CA': r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$',  # Canada
    'AU': r'^\d{4}$',  # Australia: 4 digits
    'DE': r'^\d{5}$',  # Germany: 5 digits
    'FR': r'^\d{5}$',  # France: 5 digits
    'JP': r'^\d{3}-?\d{4}$',  # Japan: 3-4 or 3+4 digits
    'CN': r'^\d{6}$',  # China: 6 digits
}

# Valid ISO-2 country codes (subset)
VALID_COUNTRY_CODES = {
    'IN', 'US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'CN',
    'BR', 'MX', 'IT', 'ES', 'NL', 'SE', 'NO', 'DK', 'FI',
    'PL', 'RO', 'CZ', 'HU', 'PT', 'GR', 'BE', 'AT', 'CH',
    'IE', 'NZ', 'SG', 'MY', 'TH', 'ID', 'PH', 'VN', 'KR',
    'TW', 'HK', 'AE', 'SA', 'IL', 'TR', 'EG', 'ZA', 'NG',
}


def validate_postal_code(postal_code: str, country: str) -> bool:
    """
    Validate postal code format for given country.
    
    Args:
        postal_code: Postal/ZIP code
        country: ISO-2 country code
    
    Returns:
        True if valid format
    """
    if not postal_code or not country:
        return True  # Allow empty
    
    country = country.upper()
    pattern = POSTAL_CODE_PATTERNS.get(country)
    
    if not pattern:
        return True  # Unknown country, allow any format
    
    return bool(re.match(pattern, postal_code.strip()))


def validate_country_code(country: str) -> bool:
    """
    Validate ISO-2 country code.
    
    Args:
        country: Country code
    
    Returns:
        True if valid
    """
    if not country:
        return False
    
    return country.upper() in VALID_COUNTRY_CODES


def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Validate latitude and longitude.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        True if valid
    """
    try:
        lat = float(lat)
        lng = float(lng)
        return -90 <= lat <= 90 and -180 <= lng <= 180
    except (ValueError, TypeError):
        return False


def validate_confidence(confidence: float) -> bool:
    """
    Validate confidence score.
    
    Args:
        confidence: Confidence value
    
    Returns:
        True if valid (0-1)
    """
    try:
        confidence = float(confidence)
        return 0 <= confidence <= 1
    except (ValueError, TypeError):
        return False


def validate_address_record(record: Dict) -> tuple[bool, List[str]]:
    """
    Validate complete address record.
    
    Args:
        record: Address record dict
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    if not record.get('company_normalized'):
        errors.append("Missing company_normalized")
    
    # Country validation
    country = record.get('country', '')
    if country and not validate_country_code(country):
        errors.append(f"Invalid country code: {country}")
    
    # Postal code validation
    postal_code = record.get('postal_code', '')
    if postal_code and country:
        if not validate_postal_code(postal_code, country):
            errors.append(f"Invalid postal code format for {country}: {postal_code}")
    
    # Coordinates validation
    lat = record.get('lat')
    lng = record.get('lng')
    if lat is not None and lng is not None:
        if not validate_coordinates(lat, lng):
            errors.append(f"Invalid coordinates: ({lat}, {lng})")
    
    # Confidence validation
    confidence = record.get('confidence')
    if confidence is not None:
        if not validate_confidence(confidence):
            errors.append(f"Invalid confidence score: {confidence}")
    
    return len(errors) == 0, errors


def assess_result_quality(parsed_result: Dict) -> Dict:
    """
    Assess quality of geocoding result.
    
    Args:
        parsed_result: Parsed geocoding result
    
    Returns:
        Dict with quality assessment
    """
    quality = {
        'score': 1.0,
        'issues': [],
        'warnings': [],
    }
    
    # Check for missing components
    required_fields = ['city', 'country']
    for field in required_fields:
        if not parsed_result.get(field):
            quality['issues'].append(f"Missing {field}")
            quality['score'] -= 0.3
    
    # Check result types
    result_types = parsed_result.get('result_types', [])
    if 'political' in result_types or 'locality' in result_types:
        quality['warnings'].append("Result is not a specific address")
        quality['score'] -= 0.1
    
    # Check postal code
    postal_code = parsed_result.get('postal_code')
    country = parsed_result.get('country')
    if postal_code and country:
        if not validate_postal_code(postal_code, country):
            quality['warnings'].append("Postal code format may be incorrect")
            quality['score'] -= 0.05
    
    # Ensure score is in valid range
    quality['score'] = max(0.0, min(1.0, quality['score']))
    
    return quality


def suggest_manual_review(record: Dict, threshold: float = 0.80) -> bool:
    """
    Determine if record should be flagged for manual review.
    
    Args:
        record: Address record
        threshold: Confidence threshold
    
    Returns:
        True if manual review recommended
    """
    confidence = record.get('confidence', 1.0)
    
    try:
        confidence = float(confidence)
    except (ValueError, TypeError):
        return True  # Invalid confidence, review needed
    
    # Low confidence
    if confidence < threshold:
        return True
    
    # Missing critical fields
    if not record.get('city') or not record.get('country'):
        return True
    
    # Validation errors
    is_valid, errors = validate_address_record(record)
    if not is_valid:
        return True
    
    return False


if __name__ == "__main__":
    # Test validation
    print("Validation Tests")
    print("=" * 60)
    
    test_records = [
        {
            'company_normalized': 'TATA CONSULTANCY SERVICES',
            'city': 'Pune',
            'country': 'IN',
            'postal_code': '411014',
            'lat': 18.5204,
            'lng': 73.8567,
            'confidence': 0.95,
        },
        {
            'company_normalized': 'INVALID COMPANY',
            'city': 'Unknown',
            'country': 'XX',  # Invalid
            'postal_code': 'INVALID',
            'lat': 200,  # Invalid
            'lng': -200,  # Invalid
            'confidence': 1.5,  # Invalid
        },
    ]
    
    for i, record in enumerate(test_records, 1):
        print(f"\nTest Record {i}:")
        is_valid, errors = validate_address_record(record)
        print(f"  Valid: {is_valid}")
        if errors:
            print(f"  Errors: {', '.join(errors)}")
        
        needs_review = suggest_manual_review(record)
        print(f"  Needs Review: {needs_review}")
