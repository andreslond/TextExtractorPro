#!/usr/bin/env python3
"""
Menu Extractor Main Script

This script orchestrates the extraction of menu items from images,
processes the text, identifies products, categories and prices,
and exports the structured data to various formats.
"""

import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from processors.ocr_processor import OCRProcessor
from processors.text_processor import TextProcessor
from models.menu_item import MenuItem, MenuCategory
from exporters.csv_exporter import CSVExporter
from exporters.json_exporter import JSONExporter
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

class MenuExtractor:
    """Main class to extract and process menu data from images."""
    
    def __init__(self, language: str = 'spa'):
        """Initialize MenuExtractor.
        
        Args:
            language: Language code for OCR (default: 'spa' for Spanish)
        """
        self.ocr_processor = OCRProcessor(language=language)
        self.text_processor = TextProcessor()
        self.csv_exporter = CSVExporter()
        self.json_exporter = JSONExporter()
    
    def process_images(self, image_paths: List[str]) -> Dict[str, List[MenuCategory]]:
        """Process multiple images and extract menu items.
        
        Args:
            image_paths: List of paths to menu images
            
        Returns:
            Dictionary mapping image filenames to extracted menu categories
        """
        results = {}
        
        for img_path in image_paths:
            try:
                filename = os.path.basename(img_path)
                logger.info(f"Processing image: {filename}")
                
                # Extract text using OCR
                extracted_text = self.ocr_processor.extract_text(img_path)
                
                if not extracted_text.strip():
                    logger.warning(f"No text extracted from {filename}")
                    continue
                
                # Process text to identify menu items and categories
                menu_categories = self.text_processor.process_text(extracted_text)
                
                results[filename] = menu_categories
                
                logger.info(f"Successfully processed {filename}: "
                           f"Found {sum(len(cat.items) for cat in menu_categories)} items "
                           f"in {len(menu_categories)} categories")
                
            except Exception as e:
                logger.error(f"Error processing {img_path}: {str(e)}", exc_info=True)
        
        return results
    
    def export_results(self, results: Dict[str, List[MenuCategory]], 
                      output_dir: str, 
                      formats: List[str] = ['csv', 'json']) -> Dict[str, str]:
        """Export processed results to specified formats.
        
        Args:
            results: Dictionary mapping image filenames to processed menu categories
            output_dir: Directory to save output files
            formats: List of export formats ('csv', 'json')
            
        Returns:
            Dictionary mapping format to output file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        output_files = {}
        
        # Flatten results for export
        all_items = []
        for filename, categories in results.items():
            for category in categories:
                for item in category.items:
                    item_dict = item.to_dict()
                    item_dict['source_image'] = filename
                    item_dict['category'] = category.name
                    all_items.append(item_dict)
        
        # Export to each requested format
        if 'csv' in formats:
            csv_path = os.path.join(output_dir, 'menu_items.csv')
            self.csv_exporter.export(all_items, csv_path)
            output_files['csv'] = csv_path
            
        if 'json' in formats:
            json_path = os.path.join(output_dir, 'menu_items.json')
            self.json_exporter.export(all_items, json_path)
            output_files['json'] = json_path
            
            # Also export hierarchical JSON with categories
            hierarchical_json_path = os.path.join(output_dir, 'menu_structure.json')
            hierarchical_data = {
                filename: [cat.to_dict() for cat in categories]
                for filename, categories in results.items()
            }
            self.json_exporter.export(hierarchical_data, hierarchical_json_path)
            output_files['hierarchical_json'] = hierarchical_json_path
            
        return output_files
    
    def get_statistics(self, results: Dict[str, List[MenuCategory]]) -> Dict[str, Any]:
        """Generate statistics from extraction results.
        
        Args:
            results: Dictionary mapping image filenames to processed menu categories
            
        Returns:
            Dictionary containing statistics
        """
        total_images = len(results)
        total_categories = sum(len(categories) for categories in results.values())
        total_items = sum(sum(len(cat.items) for cat in categories) for categories in results.values())
        
        # Calculate average prices if available
        prices = []
        for categories in results.values():
            for category in categories:
                for item in category.items:
                    if item.price is not None:
                        prices.append(item.price)
        
        avg_price = sum(prices) / len(prices) if prices else None
        min_price = min(prices) if prices else None
        max_price = max(prices) if prices else None
        
        # Category distribution
        category_counts = {}
        for categories in results.values():
            for category in categories:
                category_name = category.name
                if category_name in category_counts:
                    category_counts[category_name] += len(category.items)
                else:
                    category_counts[category_name] = len(category.items)
        
        return {
            'total_images': total_images,
            'total_categories': total_categories,
            'total_items': total_items,
            'avg_price': avg_price,
            'min_price': min_price,
            'max_price': max_price,
            'category_distribution': category_counts
        }

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract menu items from images using OCR')
    
    parser.add_argument('--images', '-i', nargs='+', required=True,
                        help='Paths to images to process')
    parser.add_argument('--output', '-o', default='output',
                        help='Output directory for extracted data')
    parser.add_argument('--formats', '-f', nargs='+', default=['csv', 'json'],
                        choices=['csv', 'json'],
                        help='Output formats (csv, json)')
    parser.add_argument('--language', '-l', default='spa',
                        help='Language code for OCR (default: spa)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    return parser.parse_args()

def main():
    """Main function to run the menu extractor."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    
    # Validate image paths
    valid_images = []
    for img_path in args.images:
        if os.path.exists(img_path):
            valid_images.append(img_path)
        else:
            logger.error(f"Image not found: {img_path}")
    
    if not valid_images:
        logger.error("No valid images provided. Exiting.")
        return
    
    # Process images
    extractor = MenuExtractor(language=args.language)
    results = extractor.process_images(valid_images)
    
    if not results:
        logger.error("No menu items were extracted. Exiting.")
        return
    
    # Export results
    output_files = extractor.export_results(results, args.output, args.formats)
    
    # Print statistics
    stats = extractor.get_statistics(results)
    logger.info("=== Extraction Statistics ===")
    logger.info(f"Processed {stats['total_images']} images")
    logger.info(f"Extracted {stats['total_items']} items in {stats['total_categories']} categories")
    
    if stats['avg_price'] is not None:
        logger.info(f"Price range: {stats['min_price']:.2f} - {stats['max_price']:.2f} (avg: {stats['avg_price']:.2f})")
    
    logger.info("Category distribution:")
    for category, count in stats['category_distribution'].items():
        logger.info(f"  {category}: {count} items")
    
    logger.info("=== Output Files ===")
    for format_name, filepath in output_files.items():
        logger.info(f"{format_name}: {filepath}")

if __name__ == "__main__":
    main()
