"""
Company name normalization module.
Applies standardization rules to company names for consistent matching.
"""
import re
import json
import unicodedata
from pathlib import Path
from typing import Dict

# Legal suffixes to strip (ordered by specificity)
LEGAL_SUFFIXES = [
    # Multi-word suffixes (check first)
    r'\bPRIVATE\s+LIMITED\b',
    r'\bPVT\.?\s*LTD\.?\b',
    r'\bPTY\.?\s*LTD\.?\b',
    r'\bL\.?\s*L\.?\s*C\.?\b',
    r'\bL\.?\s*L\.?\s*P\.?\b',
    r'\bL\.?\s*T\.?\s*D\.?\b',
    r'\bP\.?\s*L\.?\s*C\.?\b',
    r'\bINC\.?\b',
    r'\bCORP\.?\b',
    r'\bLIMITED\b',
    r'\bLTD\.?\b',
    r'\bLLC\.?\b',
    r'\bLLP\.?\b',
    r'\bGMBH\.?\b',
    r'\bS\.?\s*A\.?\s*S\.?\b',
    r'\bS\.?\s*A\.?\b',
    r'\bB\.?\s*V\.?\b',
    r'\bN\.?\s*V\.?\b',
    r'\bA\.?\s*G\.?\b',
    r'\bK\.?\s*K\.?\b',
]

# Compile regex pattern
LEGAL_SUFFIX_PATTERN = re.compile('(' + '|'.join(LEGAL_SUFFIXES) + r')$', re.IGNORECASE)

# Cache for golden mappings
_golden_mappings: Dict[str, str] = {}


def load_golden_mappings(filepath: Path = None) -> Dict[str, str]:
    """Load golden company name mappings from JSON file."""
    global _golden_mappings
    
    if _golden_mappings:
        return _golden_mappings
    
    if filepath is None:
        from . import config
        filepath = config.GOLDEN_MAPPINGS_FILE
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            _golden_mappings = json.load(f)
        return _golden_mappings
    except FileNotFoundError:
        print(f"Warning: Golden mappings file not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in golden mappings file: {e}")
        return {}


def normalize_company(name: str, use_golden_mappings: bool = True) -> str:
    """
    Normalize company name using standardization rules.
    
    Args:
        name: Raw company name
        use_golden_mappings: Whether to apply golden mapping expansions
    
    Returns:
        Normalized company name in uppercase
    
    Examples:
        >>> normalize_company("Tata Consultancy Services Ltd.")
        "TATA CONSULTANCY SERVICES"
        >>> normalize_company("HDFC Bank Pvt Ltd")
        "HDFC BANK"
        >>> normalize_company("TCS")
        "TATA CONSULTANCY SERVICES"
    """
    if not name or not isinstance(name, str):
        return ""
    
    # 1. Unicode normalization (handle special characters)
    s = unicodedata.normalize("NFKC", name)
    
    # 2. Trim and collapse whitespace
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    
    # 3. Convert to uppercase
    s = s.upper()
    
    # 4. Remove common punctuation that doesn't add meaning
    s = s.replace(',', '').replace('.', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    
    # 5. Apply golden mappings (before suffix stripping for exact matches)
    if use_golden_mappings:
        mappings = load_golden_mappings()
        # Check if the entire normalized name matches
        if s in mappings:
            return mappings[s]
        
        # Check if the name starts with a known acronym
        for acronym, full_name in sorted(mappings.items(), key=lambda x: -len(x[0])):
            if s == acronym or s.startswith(acronym + " "):
                s = s.replace(acronym, full_name, 1)
                break
    
    # 6. Strip legal suffixes
    s = LEGAL_SUFFIX_PATTERN.sub('', s).strip()
    
    # 7. Final cleanup
    s = re.sub(r'\s+', ' ', s).strip()
    
    return s


def get_normalization_variants(name: str) -> list:
    """
    Get multiple normalization variants of a company name for fuzzy matching.
    
    Args:
        name: Company name
    
    Returns:
        List of normalized variants
    """
    variants = set()
    
    # Main normalized form
    normalized = normalize_company(name)
    variants.add(normalized)
    
    # Without golden mapping
    variants.add(normalize_company(name, use_golden_mappings=False))
    
    # Remove common words
    common_words = ['THE', 'AND', 'OF', 'GROUP', 'COMPANY', 'COMPANIES']
    words = normalized.split()
    filtered = ' '.join([w for w in words if w not in common_words])
    if filtered:
        variants.add(filtered)
    
    # Just the first significant word (for very short queries)
    if words:
        variants.add(words[0])
    
    return list(variants)


def extract_acronym(name: str) -> str:
    """
    Extract potential acronym from company name.
    
    Args:
        name: Company name
    
    Returns:
        Acronym made from first letters of words
    
    Example:
        >>> extract_acronym("Tata Consultancy Services")
        "TCS"
    """
    words = name.upper().split()
    # Take first letter of each word
    acronym = ''.join([w[0] for w in words if w and w[0].isalpha()])
    return acronym


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "Tata Consultancy Services Ltd.",
        "HDFC Bank Pvt Ltd",
        "TCS",
        "IBM India Private Limited",
        "Wipro Limited",
        "Infosys Technologies Ltd.",
        "Microsoft Corporation",
        "Apple Inc.",
    ]
    
    print("Company Name Normalization Tests:")
    print("=" * 60)
    for company in test_cases:
        normalized = normalize_company(company)
        print(f"{company:40} → {normalized}")
