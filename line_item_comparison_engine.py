"""
Line Item Comparison Engine - Analyzes vendors at material level
"""
from typing import List, Dict
import pandas as pd


class LineItemComparisonEngine:
    """Analyze and rank vendors at material level"""
    
    def __init__(self, priority: str = "balanced"):
        self.priority = priority
    
    def analyze_materials(self, raw_data: List[Dict]) -> Dict:
        """Analyze vendor quotations at material level"""
        if not raw_data:
            return {"materials": [], "split_award_strategy": {
                "is_recommended": False,
                "vendor_count": 0,
                "vendor_allocation": [],
                "total_cost_split": 0,
                "total_cost_single_vendor": 0,
                "total_savings": 0,
                "savings_percentage": 0
            }}
        
        materials_data = self._group_by_material(raw_data)
        material_analysis = []
        
        for mat_code, mat_data in materials_data.items():
            analysis = self._analyze_single_material(mat_code, mat_data)
            material_analysis.append(analysis)
        
        split_award = self._calculate_split_award(material_analysis)
        
        return {
            "materials": material_analysis,
            "split_award_strategy": split_award
        }
    
    def _group_by_material(self, raw_data: List[Dict]) -> Dict[str, Dict]:
        """Group quotations by material code"""
        materials = {}
        
        for record in raw_data:
            mat_code = record['MAT_CODE']
            
            if mat_code not in materials:
                materials[mat_code] = {
                    'mat_code': mat_code,
                    'mat_text': record['MAT_TEXT'],
                    'qty': record['QTY'],
                    'uom': record['UOM'],
                    'vendor_quotes': []
                }
            
            materials[mat_code]['vendor_quotes'].append({
                'vendor_name': record['VENDOR_NAME'],
                'vendor_no': record.get('VENDOR_NO', ''), 
                'price': float(record['BASIC_PRICE']),
                'payment_terms_days': self._map_payment_term(record['PAY_TERM']),
                'delivery_days': int(record['DELIVERY_DAYS']),
                'vendor_email': record.get('VENDOR_EMAIL', ''),
                'vendor_contact_person': record.get('VENDOR_CONTACT_PERSON', ''),
                'vendor_contact_phone': record.get('VENDOR_CONTACT_PHONE', '')
            })
        
        return materials
    
    def _analyze_single_material(self, mat_code: str, mat_data: Dict) -> Dict:
        """Analyze vendor quotes for a single material"""
        vendor_quotes = mat_data['vendor_quotes']
        qty = mat_data['qty']
        
        if not vendor_quotes:
            return mat_data
        
        df = pd.DataFrame(vendor_quotes)
        df['total_value'] = df['price'] * qty
        
        # Rank vendors
        if self.priority == "low_price":
            df['score'] = (df['price'].rank(ascending=True) * 3 + df['delivery_days'].rank(ascending=True) * 1 + df['payment_terms_days'].rank(ascending=False) * 1)
        elif self.priority == "fast_delivery":
            df['score'] = (df['delivery_days'].rank(ascending=True) * 3 + df['price'].rank(ascending=True) * 1 + df['payment_terms_days'].rank(ascending=False) * 1)
        elif self.priority == "payment_terms":
            df['score'] = (df['payment_terms_days'].rank(ascending=False) * 3 + df['price'].rank(ascending=True) * 1 + df['delivery_days'].rank(ascending=True) * 1)
        else:
            df['score'] = (df['price'].rank(ascending=True) + df['delivery_days'].rank(ascending=True) + df['payment_terms_days'].rank(ascending=False))
        
        df = df.sort_values('score')
        df['rank_for_this_material'] = range(1, len(df) + 1)
        df['rank_score'] = df['score']
        
        best_price_vendor = df.loc[df['price'].idxmin(), 'vendor_name']
        best_delivery_vendor = df.loc[df['delivery_days'].idxmin(), 'vendor_name']
        best_payment_vendor = df.loc[df['payment_terms_days'].idxmax(), 'vendor_name']
        
        df['is_best_price'] = df['vendor_name'] == best_price_vendor
        df['is_best_payment'] = df['vendor_name'] == best_payment_vendor
        df['is_best_delivery'] = df['vendor_name'] == best_delivery_vendor
        
        worst_price = df['price'].max()
        best_price = df['price'].min()
        df['price_difference_from_best'] = df['price'] - best_price
        df['savings_vs_worst'] = (worst_price - df['price']) * qty
        
        recommended = df[df['rank_for_this_material'] == 1].iloc[0]
        
        alternative = None
        if len(df) > 1:
            alt_row = df[df['rank_for_this_material'] == 2].iloc[0]
            reasons = []
            if alt_row['is_best_price']: reasons.append(f"Best price (₹{alt_row['price']:.0f})")
            if alt_row['is_best_payment']: reasons.append(f"Better payment ({alt_row['payment_terms_days']}d)")
            if alt_row['is_best_delivery']: reasons.append(f"Fastest ({alt_row['delivery_days']}d)")
            alternative = {'vendor_name': alt_row['vendor_name'], 'price': float(alt_row['price']), 'reason': ' + '.join(reasons) if reasons else "Alternative"}
        
        # ========== NEW: Calculate display score for recommended vendor ==========
        total_quotes = len(df)
        max_score = 100
        min_score = 20
        
        if total_quotes > 1:
            score_range = max_score - min_score
            recommended_display_score = int(max_score - ((recommended['rank_for_this_material'] - 1) * (score_range / (total_quotes - 1))))
        else:
            recommended_display_score = max_score
        # =========================================================================
        
        return {
            'mat_code': mat_data['mat_code'],
            'mat_text': mat_data['mat_text'],
            'qty': float(mat_data['qty']),
            'uom': mat_data['uom'],
            'vendor_quotes': df.to_dict('records'),
            'recommended_vendor': {
                'vendor_name': recommended['vendor_name'],
                'vendor_no': recommended.get('vendor_no', ''), 
                'price': float(recommended['price']),
                'payment_terms_days': int(recommended['payment_terms_days']),
                'delivery_days': int(recommended['delivery_days']),
                'total_value': float(recommended['total_value']),
                'score': float(recommended['score']),
                'display_score': recommended_display_score,  # NEW: Added display score
                'reason': f"Best score ({recommended['score']:.1f})",
                'savings': float(recommended['savings_vs_worst']),
                'savings_percentage': float((worst_price - recommended['price']) / worst_price * 100) if worst_price > 0 else 0,
                'alternative': alternative
            }
        }
    
    def _calculate_split_award(self, material_analysis: List[Dict]) -> Dict:
        """Calculate optimal split-award strategy"""
        if not material_analysis:
            return {"is_recommended": False, "vendor_count": 0, "vendor_allocation": [], "total_cost_split": 0, "total_cost_single_vendor": 0, "total_savings": 0, "savings_percentage": 0, "comparison_vs_single_vendor": None}
        
        vendor_allocation = {}
        total_split_cost = 0
        
        for material in material_analysis:
            recommended = material['recommended_vendor']
            vendor_name = recommended['vendor_name']
            
            if vendor_name not in vendor_allocation:
                vendor_allocation[vendor_name] = {
                    'vendor_name': vendor_name,
                    'materials': [],
                    'material_codes': [],
                    'material_count': 0,
                    'total_value': 0,
                    'percentage_of_order': 0
                }
            
            vendor_allocation[vendor_name]['materials'].append(material['mat_code'])
            vendor_allocation[vendor_name]['material_codes'].append(material['mat_code'])
            vendor_allocation[vendor_name]['material_count'] += 1
            vendor_allocation[vendor_name]['total_value'] += recommended['total_value']
            total_split_cost += recommended['total_value']
        
        all_vendors = set()
        for material in material_analysis:
            for quote in material['vendor_quotes']:
                all_vendors.add(quote['vendor_name'])
        
        single_vendor_costs = []
        for vendor_name in all_vendors:
            total_cost = 0
            can_supply = True
            for material in material_analysis:
                quote = next((q for q in material['vendor_quotes'] if q['vendor_name'] == vendor_name), None)
                if quote:
                    total_cost += quote['total_value']
                else:
                    can_supply = False
                    break
            if can_supply:
                single_vendor_costs.append({'vendor_name': vendor_name, 'total_cost': total_cost})
        
        best_single = min(single_vendor_costs, key=lambda x: x['total_cost']) if single_vendor_costs else {'vendor_name': 'Unknown', 'total_cost': 0}
        savings = best_single['total_cost'] - total_split_cost
        savings_pct = (savings / best_single['total_cost'] * 100) if best_single['total_cost'] > 0 else 0
        
        for vendor in vendor_allocation.values():
            vendor['percentage_of_order'] = (vendor['total_value'] / total_split_cost * 100) if total_split_cost > 0 else 0
        
        return {
            "is_recommended": savings > 0 and len(vendor_allocation) > 1,
            "total_cost_split": round(total_split_cost, 2),
            "total_cost_single_vendor": round(best_single['total_cost'], 2),
            "total_savings": round(savings, 2),
            "savings_percentage": round(savings_pct, 2),
            "vendor_count": len(vendor_allocation),
            "vendor_allocation": list(vendor_allocation.values()),
            "comparison_vs_single_vendor": {
                "single_vendor_option": best_single['vendor_name'],
                "single_vendor_cost": round(best_single['total_cost'], 2),
                "split_award_cost": round(total_split_cost, 2),
                "savings": round(savings, 2),
                "savings_percentage": round(savings_pct, 2)
            }
        }
    
    def _map_payment_term(self, pay_term_code: str) -> int:
        mapping = {'00': 0,    
        '01': 90,  
        '02': 30,   
        '03': 45,   
        '04': 60, 
        '05': 90,'000': 0, '015': 15, '030': 30, '060': 60, '090': 90}
        return mapping.get(pay_term_code, 0)