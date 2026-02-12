"""
Multi-tier caching for geocoding results.
Supports in-memory and SQLite caching.
"""
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path

from .. import config


class Cache:
    """Multi-tier cache for address lookups."""
    
    def __init__(self, cache_type: str = None, db_path: str = None):
        """
        Initialize cache.
        
        Args:
            cache_type: 'memory' or 'sqlite'
            db_path: Path to SQLite database (for sqlite cache)
        """
        self.cache_type = cache_type or config.CACHE_TYPE
        self.db_path = db_path or config.CACHE_DB_PATH
        self.ttl_hours = config.CACHE_TTL_HOURS
        self.max_size = config.MAX_CACHE_SIZE
        
        # In-memory cache
        self.memory_cache: Dict[str, tuple] = {}  # key -> (value, timestamp)
        
        # SQLite cache
        if self.cache_type == 'sqlite':
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite cache database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _make_key(
        self,
        company_normalized: str,
        city: str = None,
        country: str = None,
        place_id: str = None
    ) -> str:
        """
        Create cache key from lookup parameters.
        
        Args:
            company_normalized: Normalized company name
            city: Optional city
            country: Optional country
            place_id: Optional place ID
        
        Returns:
            Cache key string
        """
        if place_id:
            return f"placeid:{place_id}"
        
        parts = [company_normalized.upper()]
        if city:
            parts.append(city.upper())
        if country:
            parts.append(country.upper())
        
        # Create hash for long keys
        key_str = '|'.join(parts)
        if len(key_str) > 100:
            hash_obj = hashlib.md5(key_str.encode())
            return f"lookup:{hash_obj.hexdigest()}"
        
        return f"lookup:{key_str}"
    
    def get(
        self,
        company_normalized: str,
        city: str = None,
        country: str = None,
        place_id: str = None
    ) -> Optional[Dict]:
        """
        Get cached address record.
        
        Args:
            company_normalized: Normalized company name
            city: Optional city
            country: Optional country
            place_id: Optional place ID
        
        Returns:
            Cached record or None
        """
        if not config.ENABLE_CACHE:
            return None
        
        key = self._make_key(company_normalized, city, country, place_id)
        
        # Try memory cache first
        if key in self.memory_cache:
            value, timestamp = self.memory_cache[key]
            if self._is_fresh(timestamp):
                return value
            else:
                # Expired, remove from memory
                del self.memory_cache[key]
        
        # Try SQLite cache
        if self.cache_type == 'sqlite':
            return self._get_from_sqlite(key)
        
        return None
    
    def set(
        self,
        record: Dict,
        company_normalized: str,
        city: str = None,
        country: str = None,
        place_id: str = None
    ):
        """
        Store address record in cache.
        
        Args:
            record: Address record to cache
            company_normalized: Normalized company name
            city: Optional city
            country: Optional country
            place_id: Optional place ID
        """
        if not config.ENABLE_CACHE:
            return
        
        key = self._make_key(company_normalized, city, country, place_id)
        timestamp = datetime.utcnow().isoformat()
        
        # Store in memory cache
        self.memory_cache[key] = (record, timestamp)
        
        # Enforce size limit
        if len(self.memory_cache) > self.max_size:
            # Remove oldest entries
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            # Keep newest 80%
            keep_count = int(self.max_size * 0.8)
            self.memory_cache = dict(sorted_items[-keep_count:])
        
        # Store in SQLite cache
        if self.cache_type == 'sqlite':
            self._set_in_sqlite(key, record, timestamp)
    
    def _get_from_sqlite(self, key: str) -> Optional[Dict]:
        """Get value from SQLite cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value, timestamp FROM cache WHERE key = ?',
                (key,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                value_json, timestamp = row
                if self._is_fresh(timestamp):
                    return json.loads(value_json)
                else:
                    # Expired, remove it
                    self._delete_from_sqlite(key)
            
            return None
        
        except Exception as e:
            print(f"SQLite cache read error: {e}")
            return None
    
    def _set_in_sqlite(self, key: str, value: Dict, timestamp: str):
        """Set value in SQLite cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)',
                (key, json.dumps(value), timestamp)
            )
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            print(f"SQLite cache write error: {e}")
    
    def _delete_from_sqlite(self, key: str):
        """Delete expired entry from SQLite cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    def _is_fresh(self, timestamp: str) -> bool:
        """Check if cached entry is still fresh."""
        try:
            cached_time = datetime.fromisoformat(timestamp)
            age = datetime.utcnow() - cached_time
            return age < timedelta(hours=self.ttl_hours)
        except Exception:
            return False
    
    def clear(self):
        """Clear all caches."""
        self.memory_cache.clear()
        
        if self.cache_type == 'sqlite':
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cache')
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error clearing SQLite cache: {e}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        memory_count = len(self.memory_cache)
        sqlite_count = 0
        
        if self.cache_type == 'sqlite':
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM cache')
                sqlite_count = cursor.fetchone()[0]
                conn.close()
            except Exception:
                pass
        
        return {
            'cache_type': self.cache_type,
            'memory_entries': memory_count,
            'sqlite_entries': sqlite_count,
            'ttl_hours': self.ttl_hours,
            'max_size': self.max_size,
        }


# Global cache instance
_cache = None

def get_cache() -> Cache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache


if __name__ == "__main__":
    # Test cache
    print("Cache Test")
    print("=" * 60)
    
    cache = Cache(cache_type='sqlite')
    
    # Test data
    test_record = {
        'company_raw': 'TCS',
        'company_normalized': 'TATA CONSULTANCY SERVICES',
        'city': 'Pune',
        'country': 'IN',
    }
    
    # Store
    cache.set(test_record, 'TATA CONSULTANCY SERVICES', 'Pune', 'IN')
    print("Stored test record")
    
    # Retrieve
    retrieved = cache.get('TATA CONSULTANCY SERVICES', 'Pune', 'IN')
    print(f"Retrieved: {retrieved}")
    
    # Stats
    stats = cache.get_stats()
    print("\nCache stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
