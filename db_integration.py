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
        # STORE THESE AS INSTANCE ATTRIBUTES!
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        
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
        # Try multiple driver paths/locations
        driver_paths = [
            # 1. First try the runtime-installed driver
            '/tmp/odbc_driver/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.so.5.1',
            # 2. Try standard driver names
            'ODBC Driver 17 for SQL Server',
            'ODBC Driver 18 for SQL Server',
            'ODBC Driver 13 for SQL Server'
        ]
        
        last_error = None
        
        for driver in driver_paths:
            try:
                # If driver is a file path (starts with /), use it directly
                if driver.startswith('/'):
                    connection_string = (
                        f"DRIVER={{{driver}}};"
                        f"SERVER={self.server};"
                        f"DATABASE={self.database};"
                        f"UID={self.username};"
                        f"PWD={self.password};"
                        f"TrustServerCertificate=yes;"
                    )
                else:
                    # It's a driver name
                    connection_string = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={self.server};"
                        f"DATABASE={self.database};"
                        f"UID={self.username};"
                        f"PWD={self.password};"
                        f"TrustServerCertificate=yes;"
                    )
                
                print(f"🔗 Trying database connection with driver: {driver}")
                conn = pyodbc.connect(connection_string, timeout=10)
                print(f"✅ Connected successfully with driver: {driver}")
                return conn
                
            except pyodbc.Error as e:
                last_error = e
                print(f"⚠️ Failed with driver '{driver}': {str(e)[:100]}...")
                continue
        
        # If all drivers failed, raise the last error
        raise Exception(f"Could not connect with any ODBC driver. Last error: {str(last_error)}")
    ''' def get_connection(self):
        """Create and return database connection"""
        return pyodbc.connect(self.connection_string)
    '''
    '''def fetch_vendor_quotations(self, rfq_no: str, plant_code: int) -> List[Dict]:
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
            h.VENDOR_NO,       
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
                for key, value in record.items():
                    if isinstance(value, Decimal):
                        record[key] = float(value)
    
                results.append(record)
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")'''
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
            h.VENDOR_NO,       
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
        WHERE h.RFQ_NO = ?       
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
                
                # Convert ALL Decimal fields to float
                for key, value in record.items():
                    if isinstance(value, Decimal):
                        record[key] = float(value)
                
                results.append(record)
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    '''def transform_to_comparison_format(self, raw_data: List[Dict]) -> List[Dict]:
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
                    'vendor_no': record.get('VENDOR_NO', ''),  # ← ADD THIS LINE!

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
                'price': float(record['BASIC_PRICE']) if record['BASIC_PRICE'] is not None else 0.0,
                'qty': float(record['QTY']) if record['QTY'] is not None else 0.0,
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
        
        return result'''
    def transform_to_comparison_format(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Transform raw database records into format expected by comparison system
        
        Groups by vendor and aggregates material prices
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
                    'vendor_no': record.get('VENDOR_NO', ''),
                    'parameters': {
                        'price': 0.0,
                        'payment_terms_days': self._map_payment_term(record['PAY_TERM']),
                        'delivery_days': int(record['DELIVERY_DAYS']) if record['DELIVERY_DAYS'] else 0
                    },
                    'materials': [],
                    'contact': {
                        'email': record.get('VENDOR_EMAIL', ''),
                        'person': record.get('VENDOR_CONTACT_PERSON', ''),
                        'phone': record.get('VENDOR_CONTACT_PHONE', '')
                    }
                }
            
            # Add material (ensure float types)
            vendors[vendor_name]['materials'].append({
                'mat_code': record['MAT_CODE'],
                'mat_text': record['MAT_TEXT'],
                'price': float(record['BASIC_PRICE']) if record['BASIC_PRICE'] is not None else 0.0,
                'qty': float(record['QTY']) if record['QTY'] is not None else 0.0,
                'uom': record['UOM']
            })
        
        # Calculate average price per vendor
        result = []
        for vendor_name, vendor_data in vendors.items():
            # Calculate weighted average price (ensure float operations)
            total_value = sum(float(m['price']) * float(m['qty']) for m in vendor_data['materials'])
            total_qty = sum(float(m['qty']) for m in vendor_data['materials'])
            avg_price = total_value / total_qty if total_qty > 0 else 0.0
            
            vendor_data['parameters']['price'] = round(float(avg_price), 2)
            result.append(vendor_data)
        
        return result
    def diagnose_missing_quotations(self, rfq_no: str, plant_code: int) -> Dict:
        """
        Diagnose why quotations are not found
        
        Returns detailed diagnostic information
        """
        diagnostics = {
            "rfq_no": rfq_no,
            "plant_code": plant_code,
            "checks": {}
        }
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check 1: Does RFQ exist in header table?
            cursor.execute("""
                SELECT COUNT(*) 
                FROM MM_PUR_VQUOT_H 
                WHERE RFQ_NO  = ? AND PLANT_CODE = ?
            """, (rfq_no, plant_code))
            header_count = cursor.fetchone()[0]
            diagnostics["checks"]["rfq_exists_in_header"] = header_count > 0
            diagnostics["checks"]["vendor_count_in_header"] = header_count
            
            # Check 2: Does RFQ have line items?
            cursor.execute("""
                SELECT COUNT(*) 
                FROM MM_PUR_VQUOT_T 
                WHERE RFQ_NO  = ? AND PLANT_CODE = ?
            """, (rfq_no, plant_code))
            line_count = cursor.fetchone()[0]
            diagnostics["checks"]["has_line_items"] = line_count > 0
            diagnostics["checks"]["line_item_count"] = line_count
            
            # Check 3: Get vendor names if header exists but no join results
            if header_count > 0:
                cursor.execute("""
                    SELECT VENDOR_NO, VENDOR_NAME 
                    FROM MM_PUR_VQUOT_H 
                    WHERE RFQ_NO  = ? AND PLANT_CODE = ?
                """, (rfq_no, plant_code))
                vendors = [{"vendor_no": row[0], "vendor_name": row[1]} for row in cursor.fetchall()]
                diagnostics["checks"]["vendors_in_header"] = vendors
            
            # Check 4: Check if materials exist in line items
            if line_count > 0:
                cursor.execute("""
                    SELECT DISTINCT MAT_CODE, MAT_TEXT 
                    FROM MM_PUR_VQUOT_T 
                    WHERE RFQ_NO  = ? AND PLANT_CODE = ?
                """, (rfq_no, plant_code))
                materials = [{"mat_code": row[0], "mat_text": row[1]} for row in cursor.fetchall()]
                diagnostics["checks"]["materials"] = materials
            
            # Check 5: Check if join would succeed
            cursor.execute("""
                SELECT COUNT(*) 
                FROM MM_PUR_VQUOT_T t
                JOIN MM_PUR_VQUOT_H h 
                    ON t.PLANT_CODE = h.PLANT_CODE 
                    AND t.FYEAR = h.FYEAR 
                    AND t.DOC_NO = h.DOC_NO
                WHERE t.RFQ_NO  = ? AND t.PLANT_CODE = ?
            """, (rfq_no, plant_code))
            join_count = cursor.fetchone()[0]
            diagnostics["checks"]["join_successful"] = join_count > 0
            diagnostics["checks"]["joined_records"] = join_count
            
            cursor.close()
            conn.close()
            
            # Generate user-friendly messages
            diagnostics["possible_reasons"] = []
            diagnostics["action_required"] = []
            
            if not diagnostics["checks"]["rfq_exists_in_header"]:
                diagnostics["possible_reasons"].append(f"RFQ {rfq_no} does not exist in system for plant {plant_code}")
                diagnostics["action_required"].append("Verify RFQ number is correct")
            
            if diagnostics["checks"]["rfq_exists_in_header"] and not diagnostics["checks"]["has_line_items"]:
                diagnostics["possible_reasons"].append("RFQ exists but has no line items")
                diagnostics["action_required"].append("Contact administrator to add materials to RFQ")
            
            if diagnostics["checks"]["rfq_exists_in_header"] and diagnostics["checks"]["has_line_items"] and not diagnostics["checks"]["join_successful"]:
                diagnostics["possible_reasons"].append("Data mismatch between header and line items (FYEAR or DOC_NO mismatch)")
                diagnostics["action_required"].append("Contact database administrator to fix data integrity")
            
            if diagnostics["checks"]["vendor_count_in_header"] == 0:
                diagnostics["possible_reasons"].append("No vendors have submitted quotations yet")
                diagnostics["action_required"].append("Wait for vendors to submit quotations")
            
            return diagnostics
            
        except Exception as e:
            return {
                "rfq_no": rfq_no,
                "plant_code": plant_code,
                "error": str(e),
                "diagnostic_failed": True
            }
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
        server="148.113.49.104,1433",
        database="dev-cmp-ps",
        username="ayaz",
        password="cmpovh@765"
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
