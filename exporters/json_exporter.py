"""
JSON Exporter Module

This module handles exporting menu data to JSON format.
"""

import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class JSONExporter:
    """Class to export menu data to JSON format."""
    
    def export(self, data: Any, output_path: str) -> bool:
        """Export menu data to JSON.
        
        Args:
            data: Data to export (list or dictionary)
            output_path: Path to save the JSON file
            
        Returns:
            Boolean indicating success
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=2)
            
            # Log details based on data type
            if isinstance(data, list):
                logger.info(f"Exported {len(data)} items to JSON: {output_path}")
            elif isinstance(data, dict):
                logger.info(f"Exported JSON data with {len(data)} top-level keys to: {output_path}")
            else:
                logger.info(f"Exported JSON data to: {output_path}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            return False
    
    def export_pretty(self, data: Any, output_path: str) -> bool:
        """Export menu data to prettified JSON with UTF-8 support.
        
        Args:
            data: Data to export (list or dictionary)
            output_path: Path to save the JSON file
            
        Returns:
            Boolean indicating success
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4, sort_keys=True)
            
            logger.info(f"Exported prettified JSON to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to prettified JSON: {str(e)}")
            return False
