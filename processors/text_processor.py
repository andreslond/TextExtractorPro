"""
Text Processor Module

This module handles the processing of extracted text to identify menu items,
categories, and prices using pattern recognition and NLP techniques.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import string
from difflib import SequenceMatcher

from models.menu_item import MenuItem, MenuCategory
from utils.text_cleaning import clean_text, normalize_text

logger = logging.getLogger(__name__)


class TextProcessor:
    """Class to process OCR-extracted text and identify menu components."""

    def __init__(self):
        """Initialize the text processor."""
        # Common words that indicate a category in Spanish/Colombian menus
        self.category_indicators = [
            # Spanish general categories
            # Colombian specific categories from example images
            'alimentacion',
            'amasijos',
            'almuerzos',
            'bebidas',
            'galleteria',
            'bebidas frias',
            'lacteos',
            'preparados',
            'parrilla',
            'snacks',
            'topping sundae',
            'wraps',
            'bolw de arros',
            'dcafe'
            'de dulce',
            'de picar'
        ]

        # Spanish words to ignore when identifying items (stop words)
        self.stopwords = [
            'con', 'y', 'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una',
            'unos', 'unas', 'en', 'para', 'por', 'a', 'al', 'o', 'u', 'sin',
            'sobre', 'desde'
        ]

        # Regular expressions for finding prices
        # Match patterns for Colombian pesos (e.g., $25,000.00, $3,900.00) and other currencies
        self.price_patterns = [
            # Colombian peso patterns (the most common from examples)
            r'\(\$([0-9,\.]+)\)',  # ($25,000.00)
            r'\(\$([0-9]+)\)',  # ($25000)
            r'\$([0-9,\.]+)\)',  # $25,000.00)
            r'\$\s*([0-9,\.]+)',  # $25,000.00

            # Price ranges with currency
            r'\$([0-9,\.]+)\s*-\s*\$([0-9,\.]+)',  # $10,000 - $25,000
        ]

        self.default_category = "Sin categoría"

        self.product_pattern = re.compile(
            r'^(.*?)\s*'  # Nombre del producto
            r'\(?\$?'  # Posibles símbolos
            r'(\d{1,3}(?:[.,]\d{3}){1,2}(?:[.,]\d{2})?)'  # Precio
            r'\)?$'  # Posible cierre
        )

    def process_text(self, text: str) -> List[MenuCategory]:
        """Process text to identify menu items and categories.
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            List of MenuCategory objects containing menu items
        """
        logger.debug("Processing extracted text")

        # Clean and normalize text
        # clean = clean_text(text)

        # Split into lines and process each line
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        logger.info(f"lines: {lines}")
        # Identify potential category headers and menu items
        categories = self._identify_categories(lines)

        # If no categories were found, create a default one
        if not categories:
            categories = [MenuCategory("Default", [])]
            current_category = categories[0]

            # Process all lines as potential menu items
            for line in lines:
                item = self._process_menu_item_line(line)
                if item:
                    current_category.items.append(item)

        # Filter out empty categories
        categories = [cat for cat in categories if cat.items]

        # Log the results
        for category in categories:
            logger.debug(
                f"Category: {category.name} with {len(category.items)} items")

        return categories

    def _identify_categories(self, lines: List[str]) -> List[MenuCategory]:
        """Identify category headers and associated menu items.
        
        Args:
            lines: List of text lines
            
        Returns:
            List of MenuCategory objects
        """
        categories = []
        current_category = None

        for i, line in enumerate(lines):
            logger.info(f"i: {i}  - line: {line}")
            # Normalize for comparison
            normalized_line = normalize_text(line.lower())

            # Check if line is a category header
            is_category = False

            # # Check for uppercase lines (common for category headers)
            # if line.isupper() and len(line) > 3:
            #    is_category = True

            # # Check for lines containing category indicator words
            # for indicator in self.category_indicators:
            #     if indicator in normalized_line:
            #         is_category = True
            #         break

            # Check for short lines followed by longer lines (likely headers)
            if (len(line.split()) <= 3 and len(line) < 20
                    and i < len(lines) - 1 and len(lines[i + 1]) > len(line)
                    and '$' not in line):
                is_category = True

            # Line with only one word and not a price
            if len(line.split()) == 1 and len(
                    line) > 3 and not self._extract_price(line):
                is_category = True

            # If we identified a category
            if is_category:
                # Clean the category name
                category_name = line.strip()
                # Remove trailing colons and dots
                category_name = re.sub(r'[:\.]+$', '', category_name)

                # Create a new category
                current_category = MenuCategory(category_name, [])
                categories.append(current_category)

            # If line is not a category and we have a current category
            elif current_category is not None:
                # Process the line as a potential menu item
                item = self._process_menu_item_line(line)
                if item:
                    current_category.items.append(item)

        return categories

    def _process_menu_item_line(self, line: str) -> Optional[MenuItem]:
        """Process a line of text as a potential menu item.
        
        Args:
            line: Text line to process
            
        Returns:
            MenuItem object or None if not a valid item
        """
        logger.info(f"Processing line: {line}")
        # Skip very short lines
        if len(line) < 3:
            return None

        # Extract the price first as it's the most reliable indicator
        product_result, price_value = self._extract_price(line)
        product_name = ''
        
        if product_result:
            product_name = product_result
            
        return MenuItem(
            name=product_name,
            price=price_value,
            description=None  # No detailed description in this line
        )

    def _extract_price(self,
                       text: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract price information from text.
        
        Args:
            text: Text to extract price from
            
        Returns:
            Tuple of (matched text, price value) or (None, None) if no price found
        """

        line = text.strip()
        if not line:
            return None, None

        matches = self.product_pattern.search(text)
        if matches:
            try:
                price_value = 0.0
                # Get the full matched text
                full_match = matches.group(0)

                logger.info(f"Match 1: {matches.group(1)}")
                logger.info(f"Match 2: {matches.group(2)}")

                product_name = matches.group(1)
                price_value = matches.group(2)[:-3].replace('.', '')

                logger.info(f"price_value: {price_value}")
                logger.info(f"full_match: {full_match}")
                return product_name, int(price_value)

            except (ValueError, IndexError):
                return None, None
        return None, None
