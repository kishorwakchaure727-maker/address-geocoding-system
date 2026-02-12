"""
Command-line interface for address lookup.
"""
import sys
import argparse
import csv
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lookup_service import get_lookup_service
from src import config


def interactive_lookup():
    """Interactive lookup mode."""
    print("=" * 60)
    print("Address Geocoding System - Interactive Mode")
    print("=" * 60)
    print("Enter company names to look up addresses.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    service = get_lookup_service()
    
    while True:
        try:
            company = input("\nCompany name: ").strip()
            
            if company.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not company:
                continue
            
            site_hint = input("Optional site hint (e.g., 'Pune, IN'): ").strip()
            
            print("\nSearching...")
            record, source = service.lookup(company, site_hint or None)
            
            if record:
                print(f"\n{'='*60}")
                print(f"Source: {source}")
                print(f"{'='*60}")
                print(f"Company: {record.get('company_normalized')}")
                print(f"Address: {record.get('street_1')}")
                if record.get('street_2'):
                    print(f"         {record.get('street_2')}")
                print(f"City: {record.get('city')}")
                print(f"State/Region: {record.get('state_region')}")
                print(f"Postal Code: {record.get('postal_code')}")
                print(f"Country: {record.get('country')}")
                print(f"Coordinates: ({record.get('lat')}, {record.get('lng')})")
                print(f"Confidence: {record.get('confidence'):.2%}")
                print(f"QA Status: {record.get('qa_status')}")
                
                if record.get('qa_status') == 'review':
                    print("\n⚠️  This result needs manual review!")
            else:
                print(f"\n✗ No results found for '{company}'")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")


def single_lookup(company: str, site_hint: str = None):
    """Single lookup command."""
    service = get_lookup_service()
    
    print(f"Looking up: {company}", end="")
    if site_hint:
        print(f", {site_hint}", end="")
    print()
    
    record, source = service.lookup(company, site_hint)
    
    if record:
        print(f"\nSource: {source}")
        print(f"Normalized: {record.get('company_normalized')}")
        print(f"Address: {record.get('street_1')}, {record.get('city')}, {record.get('country')}")
        print(f"Confidence: {record.get('confidence'):.2%}")
    else:
        print(f"✗ Not found ({source})")
        sys.exit(1)


def batch_lookup(input_file: str, output_file: str):
    """Batch lookup from CSV file."""
    print(f"Batch processing: {input_file} → {output_file}")
    
    if not Path(input_file).exists():
        print(f"✗ Input file not found: {input_file}")
        sys.exit(1)
    
    service = get_lookup_service()
    
    # Read input CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("✗ No data in input file")
        sys.exit(1)
    
    # Process each row
    results = []
    for i, row in enumerate(rows, 1):
        company = row.get('company', '').strip()
        site_hint = row.get('site_hint', '').strip()
        
        if not company:
            print(f"  {i}/{len(rows)}: Skipping (empty company)")
            continue
        
        print(f"  {i}/{len(rows)}: {company}", end=" ... ")
        
        record, source = service.lookup(company, site_hint or None)
        
        if record:
            print(f"✓ ({source})")
            results.append({
                **row,  # Include original columns
                'normalized_company': record.get('company_normalized'),
                'street_1': record.get('street_1'),
                'street_2': record.get('street_2'),
                'city': record.get('city'),
                'state_region': record.get('state_region'),
                'postal_code': record.get('postal_code'),
                'country': record.get('country'),
                'lat': record.get('lat'),
                'lng': record.get('lng'),
                'confidence': record.get('confidence'),
                'qa_status': record.get('qa_status'),
                'source': source,
            })
        else:
            print(f"✗ Not found")
            results.append({
                **row,
                'error': 'not_found',
                'source': source,
            })
    
    # Write output CSV
    if results:
        fieldnames = list(results[0].keys())
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n✓ Results saved to: {output_file}")
    else:
        print("\n✗ No results to save")


def show_stats():
    """Show system statistics."""
    service = get_lookup_service()
    stats = service.get_stats()
    
    print("\n" + "="*60)
    print("System Statistics")
    print("="*60)
    
    print("\nStorage (Google Sheets):")
    for key, value in stats['storage'].items():
        print(f"  {key}: {value}")
    
    print("\nCache:")
    for key, value in stats['cache'].items():
        print(f"  {key}: {value}")


def show_review_queue():
    """Show records needing review."""
    service = get_lookup_service()
    queue = service.get_review_queue()
    
    print(f"\nReview Queue ({len(queue)} records)")
    print("="*60)
    
    if not queue:
        print("✓ No records need review!")
        return
    
    for i, record in enumerate(queue, 1):
        print(f"\n{i}. {record.get('company_normalized')}")
        print(f"   Address: {record.get('city')}, {record.get('country')}")
        print(f"   Confidence: {record.get('confidence'):.2%}")
        print(f"   Notes: {record.get('notes', 'N/A')}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Address Geocoding & Normalization System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cli.py lookup
  
  # Single lookup
  python cli.py lookup --company "TCS" --site "Pune, India"
  
  # Batch processing
  python cli.py batch --input companies.csv --output results.csv
  
  # Show statistics
  python cli.py stats
  
  # Show review queue
  python cli.py review
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Lookup command
    lookup_parser = subparsers.add_parser('lookup', help='Look up company address')
    lookup_parser.add_argument('--company', help='Company name')
    lookup_parser.add_argument('--site', '--site-hint', dest='site_hint', help='Site hint (e.g., "Pune, India")')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch process CSV file')
    batch_parser.add_argument('--input', '-i', required=True, help='Input CSV file')
    batch_parser.add_argument('--output', '-o', required=True, help='Output CSV file')
    
    # Stats command
    subparsers.add_parser('stats', help='Show system statistics')
    
    # Review command
    subparsers.add_parser('review', help='Show review queue')
    
    args = parser.parse_args()
    
    # Validate configuration
    is_valid, errors = config.validate_config()
    if not is_valid:
        print("✗ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file and service_account.json")
        sys.exit(1)
    
    # Route to appropriate function
    if args.command == 'lookup':
        if args.company:
            single_lookup(args.company, args.site_hint)
        else:
            interactive_lookup()
    
    elif args.command == 'batch':
        batch_lookup(args.input, args.output)
    
    elif args.command == 'stats':
        show_stats()
    
    elif args.command == 'review':
        show_review_queue()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
