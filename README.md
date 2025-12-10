# Compreo Vendor Comparison FastAPI Backend

AI-powered vendor quotation analysis system that integrates with Compreo ERP SQL Server database.

## 🎯 Features

- ✅ Fetch vendor quotations from SQL Server (MM_PUR_VQUOT_H/T tables)
- ✅ Rank vendors based on price, payment terms, and delivery
- ✅ Generate AI-powered insights and recommendations
- ✅ Support for manual vendor entry
- ✅ RESTful API for Angular frontend integration
- ✅ Interactive API documentation

---

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **SQL Server ODBC Driver 17** installed
3. **OpenRouter API Key** (for AI insights - optional)

### Install ODBC Driver (Windows):
Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### Install ODBC Driver (Linux):
```bash
# Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Configure Environment (Optional - for AI insights)

```bash
# Copy template
cp .env.template .env

# Edit .env and add your OpenRouter API key
# Get free key from: https://openrouter.ai/keys
```

**Example `.env` file:**
```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
LLM_MODEL=google/gemini-2.0-flash-exp:free
```

### 3. Test Database Connection

```bash
python db_integration.py
```

**Expected output:**
```
✅ Database connection successful!
✅ Fetched 8 quotation records
✅ Transformed into 4 vendor records

Vendor: Gamma Enterprises
  Price: ₹435
  Payment: 0 days
  Delivery: 14 days
  Materials: 2
...
```

### 4. Run FastAPI Server

```bash
python main_api.py
```

**Server will start at:**
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

---

## 📚 API Endpoints

### 1. **Analyze RFQ (Database)** 
```http
POST /api/vendor-comparison/analyze
```

**Request:**
```json
{
  "rfq_no": "RFQ-2024-1001",
  "plant_code": 1100,
  "priority": "balanced"
}
```

**Response:**
```json
{
  "rfq_no": "RFQ-2024-1001",
  "plant_code": 1100,
  "priority": "balanced",
  "ranking": [
    {
      "rank": 1,
      "vendor_name": "Beta Supplies",
      "score": 6.0,
      "price": 467.5,
      "payment_terms_days": 60,
      "delivery_days": 10,
      "category_winners": ["Best Payment Terms"],
      "materials": [...]
    }
  ],
  "ai_insights": {
    "executive_summary": "Beta Supplies offers...",
    "market_intelligence": "Market analysis shows...",
    "negotiation_tips": [...]
  }
}
```

### 2. **Analyze Manual Entry**
```http
POST /api/vendor-comparison/analyze-manual
```

**Request:**
```json
{
  "vendors": [
    {
      "vendor_name": "Alpha Traders",
      "price": 150,
      "payment_terms_days": 30,
      "delivery_days": 7
    },
    {
      "vendor_name": "Beta Supplies",
      "price": 135,
      "payment_terms_days": 60,
      "delivery_days": 10
    }
  ],
  "priority": "low_price"
}
```

### 3. **Get Recent RFQs**
```http
GET /api/rfq/list?plant_code=1100&limit=10
```

### 4. **Health Check**
```http
GET /health
```

---

## 🎨 Priority Options

- **`balanced`** - Equal weight to price, payment, delivery
- **`low_price`** - 3x weight on price
- **`fast_delivery`** - 3x weight on delivery
- **`payment_terms`** - 3x weight on payment terms

---

## 🔌 Angular Integration

### Step 1: Create Service

**File: `src/app/services/vendor-comparison.service.ts`**

```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class VendorComparisonService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  analyzeRFQ(rfqNo: string, plantCode: number, priority: string = 'balanced'): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/vendor-comparison/analyze`, {
      rfq_no: rfqNo,
      plant_code: plantCode,
      priority: priority
    });
  }

  getRecentRFQs(plantCode: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/rfq/list?plant_code=${plantCode}`);
  }
}
```

### Step 2: Update Component

**File: `src/app/components/quotation-analysis.component.ts`**

```typescript
import { Component, OnInit } from '@angular/core';
import { VendorComparisonService } from '../services/vendor-comparison.service';

@Component({
  selector: 'app-quotation-analysis',
  templateUrl: './quotation-analysis.component.html'
})
export class QuotationAnalysisComponent implements OnInit {
  rfqNo: string = 'RFQ-2024-1001';
  plantCode: number = 1100;
  priority: string = 'balanced';
  
  ranking: any[] = [];
  aiInsights: any = null;
  loading: boolean = false;
  error: string = '';

  constructor(private vendorService: VendorComparisonService) {}

  ngOnInit() {
    // Component initialization
  }

  analyzeVendors() {
    this.loading = true;
    this.error = '';
    
    this.vendorService.analyzeRFQ(this.rfqNo, this.plantCode, this.priority)
      .subscribe({
        next: (response) => {
          this.ranking = response.ranking;
          this.aiInsights = response.ai_insights;
          this.loading = false;
          console.log('✅ Analysis complete', response);
        },
        error: (error) => {
          this.error = error.error?.detail || 'Analysis failed';
          this.loading = false;
          console.error('❌ Error:', error);
        }
      });
  }
}
```

### Step 3: Add Button to HTML

**File: `quotation-analysis.component.html`**

```html
<!-- Add this button to your existing page -->
<button class="pill pill-cta" (click)="analyzeVendors()" [disabled]="loading">
  {{ loading ? '🔄 Analyzing...' : '🤖 AI Vendor Analysis' }}
</button>

<!-- Display Results -->
<div *ngIf="ranking.length > 0" class="card">
  <h3>Vendor Ranking</h3>
  <table>
    <tr *ngFor="let vendor of ranking">
      <td>{{ vendor.rank }}</td>
      <td>{{ vendor.vendor_name }}</td>
      <td>₹{{ vendor.price }}</td>
      <td>{{ vendor.payment_terms_days }} days</td>
      <td>{{ vendor.delivery_days }} days</td>
    </tr>
  </table>
</div>

<div *ngIf="aiInsights" class="card">
  <h3>AI Insights</h3>
  <p>{{ aiInsights.executive_summary }}</p>
</div>
```

---

## 🔧 Troubleshooting

### Issue 1: Database Connection Failed

**Error:** `ODBC Driver not found`

**Fix:**
```bash
# Install ODBC Driver 17 (see Prerequisites section)
# Or update connection string in db_integration.py to use available driver
```

### Issue 2: AI Insights Not Working

**Error:** `AI Summary unavailable`

**Fix:**
1. Create `.env` file from template
2. Add your OpenRouter API key
3. Restart FastAPI server

**Get free API key:** https://openrouter.ai/keys

### Issue 3: CORS Error in Angular

**Error:** `Access-Control-Allow-Origin blocked`

**Fix:** FastAPI already has CORS enabled for all origins (`allow_origins=["*"]`)

In production, restrict to your Angular domain:
```python
allow_origins=["http://localhost:4200", "https://your-domain.com"]
```

### Issue 4: No Quotations Found

**Error:** `No vendor quotations found for RFQ`

**Fix:**
- Verify RFQ number exists: `SELECT * FROM MM_PUR_QUOT_H WHERE DOC_NO = 'RFQ-2024-1001'`
- Check plant code is correct
- Ensure vendors have submitted quotations

---

## 📊 Database Schema

The API queries these tables:

```sql
-- Header table
MM_PUR_VQUOT_H (vendor_no, vendor_name, pay_term, contact_info)

-- Line items table  
MM_PUR_VQUOT_T (mat_code, mat_text, basic_price, delivery_days, qty)

-- Joined by: plant_code, fyear, doc_no
```

**Payment Terms Mapping:**
- `000` = Advance payment (0 days)
- `015` = 15 days credit
- `030` = 30 days credit
- `060` = 60 days credit

---

## 🎯 Testing

### Test with cURL:

```bash
# Analyze RFQ
curl -X POST http://localhost:8000/api/vendor-comparison/analyze \
  -H "Content-Type: application/json" \
  -d '{"rfq_no": "RFQ-2024-1001", "plant_code": 1100, "priority": "balanced"}'

# Manual analysis
curl -X POST http://localhost:8000/api/vendor-comparison/analyze-manual \
  -H "Content-Type: application/json" \
  -d '{
    "vendors": [
      {"vendor_name": "Alpha", "price": 150, "payment_terms_days": 30, "delivery_days": 7},
      {"vendor_name": "Beta", "price": 135, "payment_terms_days": 60, "delivery_days": 10}
    ],
    "priority": "balanced"
  }'
```

### Test with Postman:

1. Import API: http://localhost:8000/openapi.json
2. Send requests to endpoints
3. View responses

---

## 📦 Deployment

### Production Checklist:

1. ✅ Update CORS to restrict to your domain
2. ✅ Use environment variables for database credentials
3. ✅ Enable HTTPS
4. ✅ Add authentication/authorization
5. ✅ Set up logging
6. ✅ Configure rate limiting

### Deploy to Server:

```bash
# Use gunicorn for production
pip install gunicorn

# Run with gunicorn
gunicorn main_api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## 🆘 Support

**Issues with:**
- Database connection → Check SQL Server credentials and ODBC driver
- AI insights → Verify OpenRouter API key in `.env` file
- Angular integration → Check CORS settings and API URL

**Need help?** Open an issue or contact the development team.

---

## 📝 License

Internal Compreo ERP Module - Confidential

---

**🎉 You're all set! The FastAPI backend is ready to integrate with your Angular frontend.**
