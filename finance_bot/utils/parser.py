import re
from typing import Optional, Dict, Any

# Simple local merchant cache to avoid hitting the Groq API for known entities
MERCHANT_CACHE = {
    # Food
    "zomato": {"category": "Food", "subcategory": "Food Delivery", "type": "Expense"},
    "swiggy": {"category": "Food", "subcategory": "Food Delivery", "type": "Expense"},
    "starbucks": {"category": "Food", "subcategory": "Cafe", "type": "Expense"},
    "mcdonalds": {"category": "Food", "subcategory": "Fast Food", "type": "Expense"},
    
    # Transport
    "uber": {"category": "Transport", "subcategory": "Ride Share", "type": "Expense"},
    "ola": {"category": "Transport", "subcategory": "Ride Share", "type": "Expense"},
    "petrol": {"category": "Transport", "subcategory": "Fuel", "type": "Expense"},
    "metro": {"category": "Transport", "subcategory": "Public Transit", "type": "Expense"},
    
    # Shopping / E-commerce
    "amazon": {"category": "Shopping", "subcategory": "Online Shopping", "type": "Expense"},
    "flipkart": {"category": "Shopping", "subcategory": "Online Shopping", "type": "Expense"},
    
    # Health
    "medicine": {"category": "Medicine", "subcategory": "Pharmacy", "type": "Expense"},
    "apollo": {"category": "Medicine", "subcategory": "Pharmacy", "type": "Expense"},
    
    # Bills & Subscriptions
    "netflix": {"category": "Entertainment", "subcategory": "Streaming", "type": "Expense"},
    "spotify": {"category": "Entertainment", "subcategory": "Streaming", "type": "Expense"},
    "electricity": {"category": "Bills", "subcategory": "Utilities", "type": "Expense"},
    "wifi": {"category": "Bills", "subcategory": "Internet", "type": "Expense"},
    
    # Income
    "salary": {"category": "Income", "subcategory": "Salary", "type": "Income"},
    "freelance": {"category": "Income", "subcategory": "Freelance", "type": "Income"},
    
    # Investments
    "sip": {"category": "Investment", "subcategory": "Mutual Fund", "type": "Expense"},
    "mutual fund": {"category": "Investment", "subcategory": "Mutual Fund", "type": "Expense"},
    "stocks": {"category": "Investment", "subcategory": "Stocks", "type": "Expense"},
}

def parse_transaction_locally(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to parse the transaction using local rules and cache.
    Returns a dictionary matching the Groq JSON output if successful, else None.
    Expected format: "[merchant/keyword] [amount]"
    """
    text = text.lower().strip()
    
    # Simple regex to extract word(s) and a number
    # E.g., "zomato 350", "electricity bill 1800"
    match = re.search(r"^(.*?)\s+((?:\d+)(?:\.\d+)?)$", text)
    if match:
        merchant_raw = match.group(1).strip()
        amount_raw = float(match.group(2))
        
        # Check cache
        if merchant_raw in MERCHANT_CACHE:
            cached = MERCHANT_CACHE[merchant_raw]
            return {
                "merchant": merchant_raw.title(),
                "amount": amount_raw,
                "category": cached["category"],
                "subcategory": cached["subcategory"],
                "type": cached["type"],
                "confidence": 1.0  # High confidence since it's locally cached
            }
            
    return None
