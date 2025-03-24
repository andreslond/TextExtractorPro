"""
CSV Exporter Module

This module handles exporting menu data to CSV format.
"""

import csv
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CSVExporter:
    """Class to export menu data to CSV format."""
    
    def export(self, data: List[Dict[str, Any]], output_path: str) -> bool:
        """Export menu data to CSV.
        
        Args:
            data: List of dictionaries containing menu item data
            output_path: Path to save the CSV file
            
        Returns:
            Boolean indicating success
        """
        try:
            if not data:
                logger.warning("No data to export to CSV")
                return False
            
            # Determine all possible field names from the data
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            
            # Sort fieldnames for consistent output, with core fields first
            core_fields = ['name', 'price', 'description', 'category', 'source_image']
            sorted_fields = [f for f in core_fields if f in fieldnames]
            remaining_fields = sorted(f for f in fieldnames if f not in core_fields)
            sorted_fields.extend(remaining_fields)
            
            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=sorted_fields)
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                for item in data:
                    # Ensure all fields are present
                    row = {field: item.get(field, '') for field in sorted_fields}
                    writer.writerow(row)
            
            logger.info(f"Exported {len(data)} items to CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def export_categories(self, categories: List[Dict[str, Any]], output_path: str) -> bool:
        """Export menu categories to CSV (separate files for categories and items).
        
        Args:
            categories: List of category dictionaries
            output_path: Base path for CSV files (will be appended with suffixes)
            
        Returns:
            Boolean indicating success
        """
        try:
            if not categories:
                logger.warning("No categories to export to CSV")
                return False
            
            # Create a flattened list of items with category information
            items_data = []
            for category in categories:
                category_name = category['name']
                for item in category.get('items', []):
                    item_data = item.copy()
                    item_data['category'] = category_name
                    items_data.append(item_data)
            
            # Export the items
            items_path = output_path.replace('.csv', '_items.csv')
            return self.export(items_data, items_path)
            
        except Exception as e:
            logger.error(f"Error exporting categories to CSV: {str(e)}")
            return False
