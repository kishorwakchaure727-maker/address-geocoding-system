"""
Google Sheets storage adapter.
Handles reading and writing address data to Google Sheets.
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from .. import config


class SheetsStorage:
    """Google Sheets storage adapter for address registry."""
    
    # Column schema
    COLUMNS = [
        "company_raw",
        "company_normalized",
        "site_hint",
        "street_1",
        "street_2",
        "city",
        "state_region",
        "postal_code",
        "country",
        "lat",
        "lng",
        "source",
        "confidence",
        "geocoder_place_id",
        "qa_status",
        "notes",
        "created_at",
        "updated_at",
    ]
    
    def __init__(self, sheet_id: str = None, worksheet_name: str = None, service_account_file: str = None):
        """
        Initialize Sheets storage.
        
        Args:
            sheet_id: Google Sheet ID
            worksheet_name: Name of worksheet
            service_account_file: Path to service account JSON
        """
        self.sheet_id = sheet_id or config.GOOGLE_SHEETS_ID
        self.worksheet_name = worksheet_name or config.WORKSHEET_NAME
        self.service_account_file = service_account_file or config.SERVICE_ACCOUNT_FILE
        
        if not self.sheet_id:
            raise ValueError("Google Sheets ID not configured")
        
        if not Path(self.service_account_file).exists():
            raise FileNotFoundError(f"Service account file not found: {self.service_account_file}")
        
        self.worksheet = None
        self._connect()
    
    def _connect(self):
        """Connect to Google Sheets."""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(
            self.service_account_file,
            scopes=scopes
        )
        
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(self.sheet_id)
        
        # Get or create worksheet
        try:
            self.worksheet = spreadsheet.worksheet(self.worksheet_name)
        except gspread.WorksheetNotFound:
            # Create new worksheet with headers
            self.worksheet = spreadsheet.add_worksheet(
                title=self.worksheet_name,
                rows=1000,
                cols=len(self.COLUMNS)
            )
            self.worksheet.append_row(self.COLUMNS)
            print(f"Created new worksheet: {self.worksheet_name}")
    
    def find_by_exact_match(
        self,
        company_normalized: str,
        city: str = None,
        country: str = None
    ) -> Optional[Dict]:
        """
        Find address by exact match on company name and optional location.
        
        Args:
            company_normalized: Normalized company name
            city: Optional city filter
            country: Optional country filter
        
        Returns:
            Matching record or None
        """
        all_records = self.worksheet.get_all_records()
        
        for record in all_records:
            if record['company_normalized'].upper() == company_normalized.upper():
                # Check city match if provided
                if city and record.get('city'):
                    if record['city'].upper() != city.upper():
                        continue
                
                # Check country match if provided
                if country and record.get('country'):
                    if record['country'].upper() != country.upper():
                        continue
                
                return record
        
        return None
    
    def find_by_place_id(self, place_id: str) -> Optional[Dict]:
        """
        Find address by geocoder place ID.
        
        Args:
            place_id: Geocoder place ID
        
        Returns:
            Matching record or None
        """
        if not place_id:
            return None
        
        all_records = self.worksheet.get_all_records()
        
        for record in all_records:
            if record.get('geocoder_place_id') == place_id:
                return record
        
        return None
    
    def search_fuzzy(self, company_normalized: str, country: str = None, limit: int = 5) -> List[Dict]:
        """
        Search for similar company names (fuzzy matching).
        
        Args:
            company_normalized: Normalized company name
            country: Optional country filter
            limit: Maximum results to return
        
        Returns:
            List of similar records
        """
        from rapidfuzz import fuzz
        
        all_records = self.worksheet.get_all_records()
        matches = []
        
        for record in all_records:
            # Filter by country if specified
            if country and record.get('country'):
                if record['country'].upper() != country.upper():
                    continue
            
            # Calculate similarity
            record_name = record.get('company_normalized', '')
            if not record_name:
                continue
            
            similarity = fuzz.token_set_ratio(
                company_normalized.upper(),
                record_name.upper()
            )
            
            if similarity >= 80:  # 80% threshold
                record['_similarity'] = similarity
                matches.append(record)
        
        # Sort by similarity and return top results
        matches.sort(key=lambda x: x['_similarity'], reverse=True)
        return matches[:limit]
    
    def insert(self, record: Dict) -> bool:
        """
        Insert new address record.
        
        Args:
            record: Address record dict
        
        Returns:
            True if successful
        """
        # Add timestamps
        now = datetime.utcnow().isoformat()
        record.setdefault('created_at', now)
        record.setdefault('updated_at', now)
        
        # Build row in column order
        row = [str(record.get(col, '')) for col in self.COLUMNS]
        
        try:
            self.worksheet.append_row(row)
            return True
        except Exception as e:
            print(f"Error inserting record: {e}")
            return False
    
    def update(self, company_normalized: str, updates: Dict) -> bool:
        """
        Update existing record.
        
        Args:
            company_normalized: Company name to find
            updates: Fields to update
        
        Returns:
            True if successful
        """
        # Find the row
        all_records = self.worksheet.get_all_records()
        
        for idx, record in enumerate(all_records, start=2):  # Start at 2 (1 is header)
            if record['company_normalized'].upper() == company_normalized.upper():
                # Update timestamp
                updates['updated_at'] = datetime.utcnow().isoformat()
                
                # Update cells
                for col_name, value in updates.items():
                    if col_name in self.COLUMNS:
                        col_idx = self.COLUMNS.index(col_name) + 1  # 1-indexed
                        self.worksheet.update_cell(idx, col_idx, str(value))
                
                return True
        
        return False
    
    def get_all(self, limit: int = None) -> List[Dict]:
        """
        Get all address records.
        
        Args:
            limit: Optional limit on results
        
        Returns:
            List of records
        """
        records = self.worksheet.get_all_records()
        if limit:
            return records[:limit]
        return records
    
    def get_low_confidence_records(self, threshold: float = None) -> List[Dict]:
        """
        Get records with low confidence scores requiring review.
        
        Args:
            threshold: Confidence threshold (uses config default if not provided)
        
        Returns:
            List of low-confidence records
        """
        if threshold is None:
            threshold = config.CONFIDENCE_THRESHOLD
        
        all_records = self.worksheet.get_all_records()
        low_confidence = []
        
        for record in all_records:
            try:
                confidence = float(record.get('confidence', 1.0))
                if confidence < threshold:
                    low_confidence.append(record)
            except (ValueError, TypeError):
                continue
        
        return low_confidence
    
    def get_stats(self) -> Dict:
        """
        Get storage statistics.
        
        Returns:
            Dict with stats
        """
        all_records = self.worksheet.get_all_records()
        
        total = len(all_records)
        auto = sum(1 for r in all_records if r.get('qa_status') == 'auto')
        review = sum(1 for r in all_records if r.get('qa_status') == 'review')
        
        sources = {}
        for r in all_records:
            source = r.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            'total_records': total,
            'auto_approved': auto,
            'needs_review': review,
            'sources': sources,
        }


if __name__ == "__main__":
    # Test Sheets storage
    print("Google Sheets Storage Test")
    print("=" * 60)
    
    try:
        storage = SheetsStorage()
        
        # Test stats
        stats = storage.get_stats()
        print("\nCurrent stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nConnection successful!")
    
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("  1. GOOGLE_SHEETS_ID is set in .env")
        print("  2. service_account.json file exists")
        print("  3. Sheet is shared with service account email")
