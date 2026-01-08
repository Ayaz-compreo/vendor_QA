"""
FastAPI Backend for Vendor Comparison System
Integrates with Compreo ERP SQL Server database
"""
# ================== ODBC DRIVER INSTALLATION AT RUNTIME ==================
import os
import sys
import subprocess
import platform

def install_odbc_driver_at_runtime():
    """Install ODBC Driver 17 for SQL Server when the app starts on Render."""
    
    # Skip on Windows (local development)
    if platform.system() == "Windows":
        print("⚠️ Windows detected - skipping runtime ODBC installation")
        return True
    
    print("🔧 Starting ODBC Driver runtime installation...")
    
    try:
        # Create a writable directory in /tmp
        driver_dir = "/tmp/odbc_driver"
        os.makedirs(driver_dir, exist_ok=True)
        
        print(f"📦 Downloading ODBC driver to {driver_dir}...")
        
        # Download ODBC driver .deb package
        curl_cmd = [
            'curl', '-L', '-o', f'{driver_dir}/msodbcsql.deb',
            'https://packages.microsoft.com/debian/11/prod/pool/main/m/msodbcsql17/msodbcsql17_17.10.5.1-1_amd64.deb'
        ]
        subprocess.run(curl_cmd, check=True, capture_output=True)
        
        # Extract the .deb file
        print("📂 Extracting ODBC driver package...")
        subprocess.run(['ar', 'x', f'{driver_dir}/msodbcsql.deb'], 
                      cwd=driver_dir, check=True, capture_output=True)
        
        # Extract the data.tar.xz
        if os.path.exists(f'{driver_dir}/data.tar.xz'):
            subprocess.run(['tar', '-xf', f'{driver_dir}/data.tar.xz'], 
                          cwd=driver_dir, check=True, capture_output=True)
        
        # Set LD_LIBRARY_PATH to include our extracted driver
        lib_path = f"{driver_dir}/opt/microsoft/msodbcsql17/lib64"
        if os.path.exists(lib_path):
            os.environ['LD_LIBRARY_PATH'] = lib_path + ':' + os.environ.get('LD_LIBRARY_PATH', '')
            print(f"✅ ODBC driver installed at: {lib_path}")
            
            # Verify the driver file exists
            driver_file = f"{lib_path}/libmsodbcsql-17.10.so.5.1"
            if os.path.exists(driver_file):
                print(f"✅ Driver file found: {driver_file}")
                return True
            else:
                print(f"⚠️ Driver file not found at: {driver_file}")
                return False
        else:
            print(f"⚠️ Library path not found: {lib_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Subprocess error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f"❌ Runtime ODBC installation failed: {str(e)}")
        return False

# Install ODBC driver when module loads (on Render)
ODBC_INSTALLED = install_odbc_driver_at_runtime()
print(f"ODBC Runtime Installation: {'SUCCESS' if ODBC_INSTALLED else 'FAILED'}")
# ================== END ODBC INSTALLATION ==================

"""
FastAPI Backend for Vendor Comparison System
Integrates with Compreo ERP SQL Server database
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from typing import List, Dict
from datetime import datetime
import traceback

# Import local modules
from models import (
    AnalyzeRFQRequest,
    AnalyzeManualRequest,
    ComparisonResponse,
    RankingResult,
    AIInsights,
    MaterialInfo,
    VendorContact,
    ErrorResponse,
    LineItemAnalysis
)
from db_integration import VendorQuotationDB
#from comparison_engine import VendorComparisonEngine
#from ai_engine import AIInsightsEngine
from comparison_engine_enhanced import VendorComparisonEngine
from ai_engine_enhanced import AIInsightsEngineEnhanced
from line_item_comparison_engine import LineItemComparisonEngine
from line_item_comparison_engine import LineItemComparisonEngine

# Initialize FastAPI app
app = FastAPI(
    title="Compreo Vendor Comparison API",
    description="AI-powered vendor quotation analysis for Compreo ERP",
    version="1.0.0"
)

# CORS middleware - Allow Angular app to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Angular app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    "server": "148.113.49.104,1433",
    "database": "dev-cmp-ps",
    "username": "ayaz",
    "password": "cmpovh@765"
}

# Initialize database connection
db = VendorQuotationDB(**DB_CONFIG)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Compreo Vendor Comparison API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Check database connectivity"""
    try:
        db_status = db.test_connection()
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "error",
                "error": str(e)
            }
        )


@app.post(
    "/api/vendor-comparison/analyze",
    response_model=ComparisonResponse,
    tags=["Vendor Comparison"],
    summary="Analyze RFQ vendor quotations from database"
)
def analyze_rfq(request: AnalyzeRFQRequest):
    """
    Fetch vendor quotations from database and perform enhanced comparison analysis
    
    - Fetches data from MM_PUR_VQUOT_H and MM_PUR_VQUOT_T tables
    - Ranks vendors with dimension-level scoring (VENDOR-LEVEL)
    - Analyzes best vendor per material (LINE-ITEM LEVEL)
    - Generates structured AI insights and recommendations
    
    **Returns:** Enhanced vendor analysis + Recommendations + Structured insights + Line-item analysis
    """
    try:
        # 1. Fetch vendor quotations from database
        print(f"📊 Fetching quotations for RFQ: {request.rfq_no}, Plant: {request.plant_code}")
        
        raw_data = db.fetch_vendor_quotations(request.rfq_no, request.plant_code)

        if not raw_data:
            # Run diagnostics to find out why
            diagnostics = db.diagnose_missing_quotations(request.rfq_no, request.plant_code)
            
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "No Vendor Quotations Found",
                    "message": f"No vendor quotations found for RFQ {request.rfq_no} at plant {request.plant_code}",
                    "rfq_no": request.rfq_no,
                    "plant_code": request.plant_code,
                    "diagnostics": diagnostics,
                    "help": "Please check the details below and take appropriate action"
                }
            )
        print(f"✅ Fetched {len(raw_data)} quotation records")
        
        # 2. Transform data to comparison format (VENDOR-LEVEL)
        vendors_data = db.transform_to_comparison_format(raw_data)
        print(f"✅ Transformed into {len(vendors_data)} vendors")
        
        # 3. Calculate VENDOR-LEVEL ranking with dimension scores
        from comparison_engine_enhanced import VendorComparisonEngine
        comparison_engine = VendorComparisonEngine(priority=request.priority.value)
        vendor_analysis = comparison_engine.rank_vendors(vendors_data)
        print(f"✅ Vendor-level analysis with dimension scores calculated")
        
        # 4. Calculate LINE-ITEM LEVEL analysis
        line_item_engine = LineItemComparisonEngine(priority=request.priority.value)
        line_item_data = line_item_engine.analyze_materials(raw_data)
        print(f"✅ Line-item analysis completed for {len(line_item_data['materials'])} materials")
        
        # Convert to Pydantic model
        line_item_analysis = LineItemAnalysis(**line_item_data)
        
        # 5. Generate structured AI insights and recommendations
        from ai_engine_enhanced import AIInsightsEngineEnhanced
        ai_engine = AIInsightsEngineEnhanced()
        recommendations, structured_insights, ai_insights = ai_engine.generate_structured_analysis(
            vendor_analysis, 
            request.priority.value, 
            line_item_data
        )
        print(f"✅ Generated {len(recommendations)} recommendations and {len(structured_insights)} structured insights")
        
        # 6. Build enhanced response
        response = ComparisonResponse(
            rfq_no=request.rfq_no,
            plant_code=request.plant_code,
            priority=request.priority.value,
            vendor_analysis=vendor_analysis,  # NEW: Enhanced vendor analysis
            recommendations=recommendations,   # NEW: Structured recommendations
            structured_insights=structured_insights,  # NEW: Structured insights
            line_item_analysis=line_item_analysis,
            ai_insights=ai_insights,  # Legacy, for backward compatibility
            metadata={
                "total_vendors": len(vendors_data),
                "total_materials": len(line_item_data['materials']),
                "analysis_date": datetime.now().isoformat(),
                "analysis_modes": ["vendor_level", "line_item_level", "dimension_level"]
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post(
    "/api/vendor-comparison/analyze-manual",
    response_model=ComparisonResponse,
    tags=["Vendor Comparison"],
    summary="Analyze manually entered vendor data"
)
def analyze_manual(request: AnalyzeManualRequest):
    """
    Analyze vendor comparison with manually entered data
    
    Useful for:
    - Testing without database
    - Comparing vendors from external sources
    - Quick what-if analysis
    
    **Returns:** Enhanced vendor analysis + AI insights
    """
    try:
        # Convert manual entries to comparison format
        vendors_data = []
        for vendor in request.vendors:
            vendors_data.append({
                'vendor_name': vendor.vendor_name,
                'vendor_no': '',  # No vendor number for manual entry
                'parameters': {
                    'price': vendor.price,
                    'payment_terms_days': vendor.payment_terms_days,
                    'delivery_days': vendor.delivery_days
                },
                'materials': [],
                'contact': {}
            })
        
        # Calculate enhanced vendor analysis
        comparison_engine = VendorComparisonEngine(priority=request.priority.value)
        vendor_analysis = comparison_engine.rank_vendors(vendors_data)
        
        # Generate structured AI insights
        ai_engine = AIInsightsEngineEnhanced()
        recommendations, structured_insights, ai_insights = ai_engine.generate_structured_analysis(
            vendor_analysis, 
            request.priority.value, 
            None  # No line-item data for manual entry
        )
        
        # Build enhanced response
        response = ComparisonResponse(
            priority=request.priority.value,
            vendor_analysis=vendor_analysis,  # NEW: Enhanced
            recommendations=recommendations,   # NEW
            structured_insights=structured_insights,  # NEW
            ai_insights=ai_insights,
            metadata={
                "total_vendors": len(vendors_data),
                "analysis_date": datetime.now().isoformat(),
                "source": "manual_entry",
                "analysis_modes": ["vendor_level", "dimension_level"]
            }
        )
        
        return response
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/debug/env")
def debug_env():
    """Debug environment variables"""
    import os
    return {
        "has_key": bool(os.getenv("OPENROUTER_API_KEY")),
        "key_length": len(os.getenv("OPENROUTER_API_KEY", "")),
        "model": os.getenv("LLM_MODEL", "not set")
    }

@app.get("/api/rfq/list", tags=["RFQ Management"])
def list_recent_rfqs(plant_code: int = 1100, limit: int = 10):
    """
    Get list of recent RFQs with vendor quotations
    
    Useful for Angular dropdown to select RFQ
    """
    try:
        query = """
        SELECT DISTINCT
            h.RFQ_NO,
            h.RFQ_YEAR,
            COUNT(DISTINCT h.VENDOR_NO) as VendorCount,
            MAX(h.CREATEDON) as LastUpdated
        FROM MM_PUR_VQUOT_H h
        WHERE h.PLANT_CODE = ?
        GROUP BY h.RFQ_NO, h.RFQ_YEAR
        ORDER BY MAX(h.CREATEDON) DESC
        """
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (plant_code,))
        
        results = []
        for row in cursor.fetchmany(limit):
            results.append({
                "rfq_no": row[0],
                "rfq_year": row[1],
                "vendor_count": row[2],
                "last_updated": row[3].isoformat() if row[3] else None
            })
        
        cursor.close()
        conn.close()
        
        return {"rfqs": results, "total": len(results)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch RFQ list: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Run FastAPI server
    print("🚀 Starting Compreo Vendor Comparison API...")
    print("📊 Database:", DB_CONFIG['database'])
    print("🌐 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)
