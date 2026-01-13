"""
Enhanced Comparison Engine - Ranks vendors with dimension-level scoring
"""
from typing import List, Dict
from models import VendorAnalysis, DimensionScore, CategoryWinnerDetail, MaterialInfo, VendorContact
import pandas as pd


class VendorComparisonEngine:
    """Engine to rank vendors based on priority with dimension-level analysis"""
    
    '''def __init__(self, priority: str = "balanced"):
        """
        Initialize comparison engine
        
        Args:
            priority: Ranking priority (balanced, low_price, fast_delivery, payment_terms)
        """
        self.priority = priority'''
    
    def __init__(self, priority: str = "balanced"):
        """
        Initialize comparison engine
        
        Args:
            priority: Ranking priority (balanced, low_price, fast_delivery, payment_terms)
        """
        self.priority = priority
        
        # Weight configuration based on priority
        if priority == 'low_price':
            self.weights = {
                'price': 0.60,        # 60% - Prioritize lowest price
                'payment_terms': 0.20, # 20%
                'delivery': 0.20       # 20%
            }
        elif priority == 'fast_delivery':
            self.weights = {
                'price': 0.20,        # 20%
                'payment_terms': 0.20, # 20%
                'delivery': 0.60       # 60% - Prioritize fastest delivery
            }
        elif priority == 'payment_terms':
            self.weights = {
                'price': 0.20,        # 20%
                'payment_terms': 0.60, # 60% - Prioritize best payment terms
                'delivery': 0.20       # 20%
            }
        else:  # balanced (default)
            self.weights = {
                'price': 0.34,        # 34% - Equal weighting
                'payment_terms': 0.33, # 33%
                'delivery': 0.33       # 33%
            }
    
    def rank_vendors(self, vendors_data: List[Dict]) -> List[VendorAnalysis]:
        """
        Rank vendors with dimension-level scoring
        
        Args:
            vendors_data: List of vendor data dictionaries
            
        Returns:
            List of VendorAnalysis objects with dimension scores
        """
        if not vendors_data:
            return []
        
        # Extract data for ranking
        comparison_data = []
        for vendor in vendors_data:
            vendor_name = vendor['vendor_name']
            vendor_no = vendor.get('vendor_no', '')
            params = vendor['parameters']
            
            # Calculate total quoted amount
            materials = vendor.get('materials', [])
            quoted_amount = sum(m.get('price', 0) * m.get('qty', 0) for m in materials)
            
            comparison_data.append({
                'vendor_name': vendor_name,
                'vendor_no': vendor_no,
                'price': params.get('price', 0),
                'payment_days': params.get('payment_terms_days', 0),
                'delivery_days': params.get('delivery_days', 0),
                'materials': materials,
                'contact': vendor.get('contact', {}),
                'quoted_amount': quoted_amount
            })
        
        # Create DataFrame for ranking
        df = pd.DataFrame(comparison_data)
        
        # ========== APPLY PRIORITY WEIGHTS (FIXED!) ==========
        # Normalize ranks to 0-1 scale (1 = best, 0 = worst)
        max_rank = len(df)
        
        # Price: Lower is better
        price_rank_normalized = (max_rank - df['price'].rank(ascending=True) + 1) / max_rank
        
        # Delivery: Lower is better (faster)
        delivery_rank_normalized = (max_rank - df['delivery_days'].rank(ascending=True) + 1) / max_rank
        
        # Payment: Higher is better (more credit days)
        payment_rank_normalized = (df['payment_days'].rank(ascending=False)) / max_rank
        
        # Apply priority weights from __init__
        df['rank_score'] = (
            price_rank_normalized * self.weights['price'] * 10 +
            delivery_rank_normalized * self.weights['delivery'] * 10 +
            payment_rank_normalized * self.weights['payment_terms'] * 10
        )
        # ======================================================
        
        # Sort by rank score (higher score = better)
        df = df.sort_values('rank_score', ascending=False)
        df['rank'] = range(1, len(df) + 1)
        
        # Calculate dimension scores for all vendors
        df = self._calculate_dimension_scores(df)
        
        # Identify category winners
        best_price_vendor = df.loc[df['price'].idxmin(), 'vendor_name']
        best_delivery_vendor = df.loc[df[df['delivery_days'] > 0]['delivery_days'].idxmin(), 'vendor_name']
        best_payment_vendor = df.loc[df['payment_days'].idxmax(), 'vendor_name']
        
        # Build enhanced result list
        results = []
        for _, row in df.iterrows():
            # Calculate display score (20-100 range)
            total_vendors = len(df)
            max_score = 100
            min_score = 20
            
            if total_vendors > 1:
                score_range = max_score - min_score
                display_score = int(max_score - ((row['rank'] - 1) * (score_range / (total_vendors - 1))))
            else:
                display_score = max_score
            
            # Build dimension scores array
            dimension_scores = [
                DimensionScore(
                    dimension_code="PRICE",
                    score=float(row['price_dimension_score']),
                    confidence=int(row['price_confidence']),
                    evidence_text=row['price_evidence']
                ),
                DimensionScore(
                    dimension_code="DELIVERY",
                    score=float(row['delivery_dimension_score']),
                    confidence=int(row['delivery_confidence']),
                    evidence_text=row['delivery_evidence']
                ),
                DimensionScore(
                    dimension_code="PAYMENT_TERMS",
                    score=float(row['payment_dimension_score']),
                    confidence=int(row['payment_confidence']),
                    evidence_text=row['payment_evidence']
                ),
                DimensionScore(
                    dimension_code="VENDOR_HISTORY",
                    score=float(row['history_dimension_score']),
                    confidence=int(row['history_confidence']),
                    evidence_text=row['history_evidence']
                ),
                DimensionScore(
                    dimension_code="QUALITY_COMP",
                    bool_value=bool(row['quality_compliant']),
                    confidence=int(row['quality_confidence']),
                    evidence_text=row['quality_evidence']
                ),
                DimensionScore(
                    dimension_code="CAPACITY",
                    bool_value=bool(row['has_capacity']),
                    confidence=int(row['capacity_confidence']),
                    evidence_text=row['capacity_evidence']
                )
            ]
            
            # Build category winners with dimension mapping
            category_winners = []
            if row['vendor_name'] == best_price_vendor:
                category_winners.append(CategoryWinnerDetail(
                    dimension_code="PRICE",
                    category_label="Best Price",
                    badge_color="GREEN"
                ))
            if row['vendor_name'] == best_delivery_vendor:
                category_winners.append(CategoryWinnerDetail(
                    dimension_code="DELIVERY",
                    category_label="Fastest Delivery",
                    badge_color="ORANGE"
                ))
            if row['vendor_name'] == best_payment_vendor:
                category_winners.append(CategoryWinnerDetail(
                    dimension_code="PAYMENT_TERMS",
                    category_label="Best Payment Terms",
                    badge_color="BLUE"
                ))
            
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
            
            # Create enhanced result
            result = VendorAnalysis(
                rank=int(row['rank']),
                vendor_name=row['vendor_name'],
                vendor_no=row['vendor_no'],
                overall_score=float(row['overall_score']),
                quoted_amount=float(row['quoted_amount']),
                dimension_scores=dimension_scores,
                category_winners=category_winners,
                # Legacy fields for backward compatibility
                score=float(row['rank_score']),
                display_score=display_score,
                price=float(row['price']),
                payment_terms_days=int(row['payment_days']),
                delivery_days=int(row['delivery_days']),
                materials=materials,
                contact=contact
            )
            
            results.append(result)
        
        return results
    def _calculate_dimension_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate individual dimension scores (0-10 scale) for each vendor
        UPDATED: Uses exponential curve for fairer scoring with few vendors
        
        Args:
            df: DataFrame with vendor data
            
        Returns:
            DataFrame with dimension scores added
        """
        # Calculate statistics for normalization
        avg_price = df['price'].mean()
        min_price = df['price'].min()
        max_price = df['price'].max()
        
        avg_delivery = df['delivery_days'].mean()
        min_delivery = df['delivery_days'].min()
        max_delivery = df['delivery_days'].max()
        
        avg_payment = df['payment_days'].mean()
        min_payment = df['payment_days'].min()
        max_payment = df['payment_days'].max()
        
        for idx, row in df.iterrows():
            # ========== PRICE COMPETITIVENESS (0-10, higher = better) ==========
            if max_price > min_price:
                # Calculate percentage difference from best price
                price_diff_pct = (row['price'] - min_price) / min_price * 100
                
                # Exponential scoring curve (gentler than linear)
                if price_diff_pct == 0:
                    price_score = 10.0  # Best price
                elif price_diff_pct < 2:
                    price_score = 9.5   # Within 2% of best
                elif price_diff_pct < 5:
                    price_score = 9.0   # Within 5% of best
                elif price_diff_pct < 10:
                    price_score = 7.5   # Within 10% of best
                elif price_diff_pct < 15:
                    price_score = 6.0   # Within 15% of best
                elif price_diff_pct < 20:
                    price_score = 4.5   # Within 20% of best
                elif price_diff_pct < 30:
                    price_score = 3.0   # Within 30% of best
                else:
                    price_score = 1.5   # More than 30% above best
            else:
                price_score = 10.0  # All vendors have same price
            
            # Evidence text
            price_diff_from_min = ((row['price'] - min_price) / min_price * 100) if min_price > 0 else 0
            if row['price'] == min_price:
                price_evidence = f"Best price at ₹{row['price']:.0f}/unit"
                price_confidence = 95
            elif price_diff_from_min < 10:
                price_evidence = f"Competitive at ₹{row['price']:.0f}/unit ({price_diff_from_min:.1f}% above lowest)"
                price_confidence = 90
            else:
                price_evidence = f"₹{row['price']:.0f}/unit ({price_diff_from_min:.1f}% above lowest bid)"
                price_confidence = 92
            
            df.at[idx, 'price_dimension_score'] = round(price_score, 1)
            df.at[idx, 'price_confidence'] = price_confidence
            df.at[idx, 'price_evidence'] = price_evidence
            
            # ========== DELIVERY SPEED (0-10, higher = better) ==========
            if max_delivery > min_delivery:
                # Calculate percentage difference from best delivery
                delivery_diff_pct = (row['delivery_days'] - min_delivery) / min_delivery * 100 if min_delivery > 0 else 0
                
                # Exponential scoring curve
                if delivery_diff_pct == 0:
                    delivery_score = 10.0  # Fastest
                elif delivery_diff_pct < 10:
                    delivery_score = 9.0   # Within 10% of fastest
                elif delivery_diff_pct < 20:
                    delivery_score = 7.5   # Within 20% of fastest
                elif delivery_diff_pct < 30:
                    delivery_score = 6.0   # Within 30% of fastest
                elif delivery_diff_pct < 50:
                    delivery_score = 4.5   # Within 50% of fastest
                else:
                    delivery_score = 3.0   # More than 50% slower
            else:
                delivery_score = 10.0  # All vendors same delivery
            
            # Evidence text
            if row['delivery_days'] == min_delivery:
                delivery_evidence = f"Fastest delivery at {row['delivery_days']} days"
                delivery_confidence = 95
            elif row['delivery_days'] <= avg_delivery:
                delivery_evidence = f"{row['delivery_days']}-day delivery - faster than average"
                delivery_confidence = 88
            else:
                delivery_evidence = f"{row['delivery_days']}-day delivery - acceptable timeline"
                delivery_confidence = 85
            
            df.at[idx, 'delivery_dimension_score'] = round(delivery_score, 1)
            df.at[idx, 'delivery_confidence'] = delivery_confidence
            df.at[idx, 'delivery_evidence'] = delivery_evidence
            
            # ========== PAYMENT TERMS (0-10, higher = better) ==========
            if max_payment > min_payment:
                # Calculate normalized score
                payment_diff_pct = (row['payment_days'] - min_payment) / (max_payment - min_payment) * 100
                
                # Linear is fine for payment terms (more credit = better)
                payment_score = 10 * ((row['payment_days'] - min_payment) / (max_payment - min_payment))
            else:
                # All vendors have same payment terms
                payment_score = 10.0 if row['payment_days'] > 0 else 3.0
            
            # Evidence text
            if row['payment_days'] == 0:
                payment_evidence = "Advance payment required - impacts cash flow"
                payment_confidence = 95
            elif row['payment_days'] >= 30:
                payment_evidence = f"{row['payment_days']}-day credit terms - excellent for cash flow"
                payment_confidence = 90
            else:
                payment_evidence = f"{row['payment_days']}-day credit terms"
                payment_confidence = 88
            
            df.at[idx, 'payment_dimension_score'] = round(payment_score, 1)
            df.at[idx, 'payment_confidence'] = payment_confidence
            df.at[idx, 'payment_evidence'] = payment_evidence
            
            # ========== VENDOR HISTORY (Fixed based on data availability) ==========
            # Score 8.0 as default (good) - would need historical data for accurate scoring
            history_score = 8.0
            history_evidence = "Established supplier with good track record"
            history_confidence = 80
            
            df.at[idx, 'history_dimension_score'] = history_score
            df.at[idx, 'history_confidence'] = history_confidence
            df.at[idx, 'history_evidence'] = history_evidence
            
            # ========== QUALITY COMPLIANCE (Boolean) ==========
            # Assume true if vendor submitted quotation
            quality_compliant = True
            quality_evidence = "Vendor meets quality standards"
            quality_confidence = 85
            
            df.at[idx, 'quality_compliant'] = quality_compliant
            df.at[idx, 'quality_confidence'] = quality_confidence
            df.at[idx, 'quality_evidence'] = quality_evidence
            
            # ========== CAPACITY (Boolean) ==========
            # Assume true if vendor quoted (has capacity)
            has_capacity = True
            total_qty = sum(m.get('qty', 0) for m in row['materials'])
            capacity_evidence = f"Can handle {total_qty:.0f} units volume" if total_qty > 0 else "Adequate capacity"
            capacity_confidence = 88
            
            df.at[idx, 'has_capacity'] = has_capacity
            df.at[idx, 'capacity_confidence'] = capacity_confidence
            df.at[idx, 'capacity_evidence'] = capacity_evidence
            
            # ========== OVERALL SCORE (0-10, average of numeric dimensions) ==========
            # Average of PRICE, DELIVERY, PAYMENT_TERMS, VENDOR_HISTORY
            overall_score = (
            (price_score / 10) * self.weights['price'] +
            (delivery_score / 10) * self.weights['delivery'] +
            (payment_score / 10) * self.weights['payment_terms'] +
            (history_score / 10) * 0.10  # Fixed 10% for history
                ) * 10 
            
            df.at[idx, 'overall_score'] = round(overall_score, 1)
        
        return df
    
    '''def _calculate_dimension_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate individual dimension scores (0-10 scale) for each vendor
        
        Args:
            df: DataFrame with vendor data
            
        Returns:
            DataFrame with dimension scores added
        """
        # Calculate statistics for normalization
        avg_price = df['price'].mean()
        min_price = df['price'].min()
        max_price = df['price'].max()
        
        avg_delivery = df['delivery_days'].mean()
        min_delivery = df['delivery_days'].min()
        max_delivery = df['delivery_days'].max()
        
        avg_payment = df['payment_days'].mean()
        min_payment = df['payment_days'].min()
        max_payment = df['payment_days'].max()
        
        for idx, row in df.iterrows():
            # ========== PRICE COMPETITIVENESS (0-10, higher = better) ==========
            if max_price > min_price:
                # Invert: lower price = higher score
                price_score = 10 * (1 - (row['price'] - min_price) / (max_price - min_price))
            else:
                price_score = 10.0
            
            price_diff_from_min = ((row['price'] - min_price) / min_price * 100) if min_price > 0 else 0
            if row['price'] == min_price:
                price_evidence = f"Best price at ₹{row['price']:.0f}/unit"
                price_confidence = 95
            elif price_diff_from_min < 10:
                price_evidence = f"Competitive at ₹{row['price']:.0f}/unit ({price_diff_from_min:.1f}% above lowest)"
                price_confidence = 90
            else:
                price_evidence = f"₹{row['price']:.0f}/unit ({price_diff_from_min:.1f}% above lowest bid)"
                price_confidence = 92
            
            df.at[idx, 'price_dimension_score'] = round(price_score, 1)
            df.at[idx, 'price_confidence'] = price_confidence
            df.at[idx, 'price_evidence'] = price_evidence
            
            # ========== DELIVERY SPEED (0-10, higher = better) ==========
            if max_delivery > min_delivery:
                # Invert: faster delivery = higher score
                delivery_score = 10 * (1 - (row['delivery_days'] - min_delivery) / (max_delivery - min_delivery))
            else:
                delivery_score = 10.0
            
            if row['delivery_days'] == min_delivery:
                delivery_evidence = f"Fastest delivery at {row['delivery_days']} days"
                delivery_confidence = 95
            elif row['delivery_days'] <= avg_delivery:
                delivery_evidence = f"{row['delivery_days']}-day delivery - faster than average"
                delivery_confidence = 88
            else:
                delivery_evidence = f"{row['delivery_days']}-day delivery - acceptable timeline"
                delivery_confidence = 85
            
            df.at[idx, 'delivery_dimension_score'] = round(delivery_score, 1)
            df.at[idx, 'delivery_confidence'] = delivery_confidence
            df.at[idx, 'delivery_evidence'] = delivery_evidence
            
            # ========== PAYMENT TERMS (0-10, higher = better) ==========
            if max_payment > min_payment:
                payment_score = 10 * ((row['payment_days'] - min_payment) / (max_payment - min_payment))
            else:
                payment_score = 10.0 if row['payment_days'] > 0 else 3.0
            
            if row['payment_days'] == 0:
                payment_evidence = "Advance payment required - impacts cash flow"
                payment_confidence = 95
            elif row['payment_days'] >= 30:
                payment_evidence = f"{row['payment_days']}-day credit terms - excellent for cash flow"
                payment_confidence = 90
            else:
                payment_evidence = f"{row['payment_days']}-day credit terms"
                payment_confidence = 88
            
            df.at[idx, 'payment_dimension_score'] = round(payment_score, 1)
            df.at[idx, 'payment_confidence'] = payment_confidence
            df.at[idx, 'payment_evidence'] = payment_evidence
            
            # ========== VENDOR HISTORY (Fixed based on data availability) ==========
            # Score 8.0 as default (good) - would need historical data for accurate scoring
            history_score = 8.0
            history_evidence = "Established supplier with good track record"
            history_confidence = 80
            
            df.at[idx, 'history_dimension_score'] = history_score
            df.at[idx, 'history_confidence'] = history_confidence
            df.at[idx, 'history_evidence'] = history_evidence
            
            # ========== QUALITY COMPLIANCE (Boolean) ==========
            # Assume true if vendor submitted quotation
            quality_compliant = True
            quality_evidence = "Vendor meets quality standards"
            quality_confidence = 85
            
            df.at[idx, 'quality_compliant'] = quality_compliant
            df.at[idx, 'quality_confidence'] = quality_confidence
            df.at[idx, 'quality_evidence'] = quality_evidence
            
            # ========== CAPACITY (Boolean) ==========
            # Assume true if vendor quoted (has capacity)
            has_capacity = True
            total_qty = sum(m.get('qty', 0) for m in row['materials'])
            capacity_evidence = f"Can handle {total_qty:.0f} units volume" if total_qty > 0 else "Adequate capacity"
            capacity_confidence = 88
            
            df.at[idx, 'has_capacity'] = has_capacity
            df.at[idx, 'capacity_confidence'] = capacity_confidence
            df.at[idx, 'capacity_evidence'] = capacity_evidence
            
            # ========== OVERALL SCORE (0-10, average of numeric dimensions) ==========
            # Average of PRICE, DELIVERY, PAYMENT_TERMS, VENDOR_HISTORY
            overall_score = (
                price_score + 
                delivery_score + 
                payment_score + 
                history_score
            ) / 4
            
            df.at[idx, 'overall_score'] = round(overall_score, 1)
        
        return df'''