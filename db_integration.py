"""
Database Integration Module
Connects to SQL Server and fetches vendor quotation data
"""
import pyodbc
from typing import List, Dict, Optional
from decimal import Decimal


class VendorQuotationDB:
    """Handle all database operations for vendor quotations"""
    
    def __init__(self, server: str, database: str, username: str, password: str):
        """Initialize database connection"""
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
        )
        
    def get_connection(self):
        """Create and return database connection"""
        return pyodbc.connect(self.connection_string)
    
    def fetch_vendor_quotations(self, rfq_no: str, plant_code: int) -> List[Dict]:
        """
        Fetch all vendor quotations for a given RFQ
        
        Args:
            rfq_no: RFQ number (e.g., 'RFQ-2024-1001')
            plant_code: Plant code (e.g., 1100)
            
        Returns:
            List of vendor quotation records
        """
        query = """
        SELECT 
            h.VENDOR_NAME,
            h.PAY_TERM,
            h.VENDOR_EMAIL,
            h.VENDOR_CONTACT_PERSON,
            h.VENDOR_CONTACT_PHONE,
            t.MAT_CODE,
            t.MAT_TEXT,
            t.BASIC_PRICE,
            t.DELIVERY_DAYS,
            t.QTY,
            t.UOM
        FROM MM_PUR_VQUOT_T t
        JOIN MM_PUR_VQUOT_H h 
            ON t.PLANT_CODE = h.PLANT_CODE 
            AND t.FYEAR = h.FYEAR 
            AND t.DOC_NO = h.DOC_NO
        WHERE t.RFQ_NO = ? 
            AND t.PLANT_CODE = ?
        ORDER BY t.MAT_CODE, t.BASIC_PRICE
        """
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (rfq_no, plant_code))
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                # Convert Decimal to float for JSON serialization
                if isinstance(record.get('BASIC_PRICE'), Decimal):
                    record['BASIC_PRICE'] = float(record['BASIC_PRICE'])
                if isinstance(record.get('QTY'), Decimal):
                    record['QTY'] = float(record['QTY'])
                results.append(record)
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def transform_to_comparison_format(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Transform raw database records into format expected by comparison system
        
        Groups by vendor and aggregates material prices
        
        Args:
            raw_data: Raw records from database
            
        Returns:
            List of vendor data in comparison format
        """
        if not raw_data:
            return []
        
        # Group by vendor
        vendors = {}
        
        for record in raw_data:
            vendor_name = record['VENDOR_NAME']
            
            if vendor_name not in vendors:
                vendors[vendor_name] = {
                    'vendor_name': vendor_name,
                    'parameters': {
                        'price': 0.0,  # Will calculate average
                        'payment_terms_days': self._map_payment_term(record['PAY_TERM']),
                        'delivery_days': record['DELIVERY_DAYS']
                    },
                    'materials': [],
                    'contact': {
                        'email': record.get('VENDOR_EMAIL', ''),
                        'person': record.get('VENDOR_CONTACT_PERSON', ''),
                        'phone': record.get('VENDOR_CONTACT_PHONE', '')
                    }
                }
            
            # Add material
            vendors[vendor_name]['materials'].append({
                'mat_code': record['MAT_CODE'],
                'mat_text': record['MAT_TEXT'],
                'price': record['BASIC_PRICE'],
                'qty': record['QTY'],
                'uom': record['UOM']
            })
        
        # Calculate average price per vendor (for comparison)
        result = []
        for vendor_name, vendor_data in vendors.items():
            # Calculate weighted average price
            total_value = sum(m['price'] * m['qty'] for m in vendor_data['materials'])
            total_qty = sum(m['qty'] for m in vendor_data['materials'])
            avg_price = total_value / total_qty if total_qty > 0 else 0
            
            vendor_data['parameters']['price'] = round(avg_price, 2)
            result.append(vendor_data)
        
        return result
    
    def _map_payment_term(self, pay_term_code: str) -> int:
        """
        Map payment term code to number of days
        
        Args:
            pay_term_code: Payment term code (e.g., '030', '060', '000')
            
        Returns:
            Number of days
        """
        payment_mapping = {
            '000': 0,    # Advance payment
            '015': 15,   # 15 days credit
            '030': 30,   # 30 days credit
            '060': 60,   # 60 days credit
            '090': 90,   # 90 days credit
        }
        
        return payment_mapping.get(pay_term_code, 0)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    # Test the database connection
    db = VendorQuotationDB(
        server="20.204.64.39,14333",
        database="sit-cmp-projectsystems",
        username="ayaz@cmp",
        password="ayaz@cmp123"
    )
    
    # Test connection
    if db.test_connection():
        print("✅ Database connection successful!")
        
        # Fetch quotations
        try:
            quotations = db.fetch_vendor_quotations("RFQ-2024-1001", 1100)
            print(f"\n✅ Fetched {len(quotations)} quotation records")
            
            # Transform to comparison format
            vendors = db.transform_to_comparison_format(quotations)
            print(f"\n✅ Transformed into {len(vendors)} vendor records")
            
            # Display
            for vendor in vendors:
                print(f"\nVendor: {vendor['vendor_name']}")
                print(f"  Price: ₹{vendor['parameters']['price']}")
                print(f"  Payment: {vendor['parameters']['payment_terms_days']} days")
                print(f"  Delivery: {vendor['parameters']['delivery_days']} days")
                print(f"  Materials: {len(vendor['materials'])}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        print("❌ Database connection failed!")
