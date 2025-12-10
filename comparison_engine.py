"""
Comparison Engine - Ranks vendors based on price, payment, delivery
"""
from typing import List, Dict
from models import RankingResult, MaterialInfo, VendorContact
import pandas as pd


class VendorComparisonEngine:
    """Engine to rank vendors based on priority"""
    
    def __init__(self, priority: str = "balanced"):
        """
        Initialize comparison engine
        
        Args:
            priority: Ranking priority (balanced, low_price, fast_delivery, payment_terms)
        """
        self.priority = priority
    
    def rank_vendors(self, vendors_data: List[Dict]) -> List[RankingResult]:
        """
        Rank vendors based on price, payment terms, and delivery
        
        Args:
            vendors_data: List of vendor data dictionaries
            
        Returns:
            List of RankingResult objects sorted by rank
        """
        if not vendors_data:
            return []
        
        # Extract data for ranking
        comparison_data = []
        for vendor in vendors_data:
            vendor_name = vendor['vendor_name']
            params = vendor['parameters']
            
            comparison_data.append({
                'vendor_name': vendor_name,
                'price': params.get('price', 0),
                'payment_days': params.get('payment_terms_days', 0),
                'delivery_days': params.get('delivery_days', 0),
                'materials': vendor.get('materials', []),
                'contact': vendor.get('contact', {})
            })
        
        # Create DataFrame for ranking
        df = pd.DataFrame(comparison_data)
        
        # Calculate ranks based on priority
        if self.priority == "low_price":
            # Price is most important (3x weight)
            df['rank_score'] = (
                df['price'].rank(ascending=True) * 3 +  # Lower price = better
                df['delivery_days'].rank(ascending=True) * 1 +  # Faster delivery = better
                df['payment_days'].rank(ascending=False) * 1  # More days = better
            )
        elif self.priority == "fast_delivery":
            # Delivery is most important (3x weight)
            df['rank_score'] = (
                df['delivery_days'].rank(ascending=True) * 3 +  # Faster = better
                df['price'].rank(ascending=True) * 1 +
                df['payment_days'].rank(ascending=False) * 1
            )
        elif self.priority == "payment_terms":
            # Payment terms is most important (3x weight)
            df['rank_score'] = (
                df['payment_days'].rank(ascending=False) * 3 +  # More days = better
                df['price'].rank(ascending=True) * 1 +
                df['delivery_days'].rank(ascending=True) * 1
            )
        else:  # balanced
            # All equal weight
            df['rank_score'] = (
                df['price'].rank(ascending=True) +
                df['delivery_days'].rank(ascending=True) +
                df['payment_days'].rank(ascending=False)
            )
        
        # Sort by rank score
        df = df.sort_values('rank_score')
        df['rank'] = range(1, len(df) + 1)
        
        # Identify category winners
        best_price_vendor = df.loc[df['price'].idxmin(), 'vendor_name']
        best_delivery_vendor = df.loc[df[df['delivery_days'] > 0]['delivery_days'].idxmin(), 'vendor_name']
        best_payment_vendor = df.loc[df['payment_days'].idxmax(), 'vendor_name']
        
        # Build result list
        results = []
        for _, row in df.iterrows():
            # Determine category winners
            category_winners = []
            if row['vendor_name'] == best_price_vendor:
                category_winners.append("Best Price")
            if row['vendor_name'] == best_delivery_vendor:
                category_winners.append("Fastest Delivery")
            if row['vendor_name'] == best_payment_vendor:
                category_winners.append("Best Payment Terms")
            
            # Convert materials list
            materials = [
                MaterialInfo(
                    mat_code=m.get('mat_code', ''),
                    mat_text=m.get('mat_text', ''),
                    price=float(m.get('price', 0)),
                    qty=float(m.get('qty', 0)),
                    uom=m.get('uom', '')
                )
                for m in row['materials']
            ]
            
            # Convert contact info
            contact_data = row['contact']
            contact = VendorContact(
                email=contact_data.get('email', ''),
                person=contact_data.get('person', ''),
                phone=contact_data.get('phone', '')
            )
            
            # Create result
            result = RankingResult(
                rank=int(row['rank']),
                vendor_name=row['vendor_name'],
                score=float(row['rank_score']),
                price=float(row['price']),
                payment_terms_days=int(row['payment_days']),
                delivery_days=int(row['delivery_days']),
                category_winners=category_winners,
                materials=materials,
                contact=contact
            )
            
            results.append(result)
        
        return results
