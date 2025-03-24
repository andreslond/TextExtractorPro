"""
Menu Item Model Module

This module defines data structures for representing menu items and categories.
"""

from typing import List, Dict, Any, Optional

class MenuItem:
    """Class representing a menu item."""
    
    def __init__(self, name: str, price: Optional[float] = None, description: Optional[str] = None):
        """Initialize a MenuItem.
        
        Args:
            name: Name of the menu item
            price: Price of the item (optional)
            description: Description of the item (optional)
        """
        self.name = name
        self.price = price
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the MenuItem to a dictionary.
        
        Returns:
            Dictionary representation of the MenuItem
        """
        return {
            'name': self.name,
            'price': self.price,
            'description': self.description
        }
    
    def __str__(self) -> str:
        """Get string representation of the MenuItem.
        
        Returns:
            String representation
        """
        price_str = f"{self.price:.2f}" if self.price is not None else "N/A"
        desc_str = f": {self.description}" if self.description else ""
        return f"{self.name} - {price_str}€{desc_str}"


class MenuCategory:
    """Class representing a category of menu items."""
    
    def __init__(self, name: str, items: List[MenuItem]):
        """Initialize a MenuCategory.
        
        Args:
            name: Name of the category
            items: List of MenuItems in this category
        """
        self.name = name
        self.items = items
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the MenuCategory to a dictionary.
        
        Returns:
            Dictionary representation of the MenuCategory
        """
        return {
            'name': self.name,
            'items': [item.to_dict() for item in self.items]
        }
    
    def __str__(self) -> str:
        """Get string representation of the MenuCategory.
        
        Returns:
            String representation
        """
        items_str = '\n  '.join(str(item) for item in self.items)
        return f"{self.name}:\n  {items_str}"
