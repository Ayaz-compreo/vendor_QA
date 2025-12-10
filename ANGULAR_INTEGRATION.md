# 🎨 ANGULAR INTEGRATION GUIDE - AI Insights Mapping

## 📊 **API Response Structure**

The FastAPI backend now returns **4 detailed AI sections** that map directly to your Angular page:

```json
{
  "rfq_no": "RFQ-2024-1001",
  "plant_code": 1100,
  "priority": "balanced",
  "ranking": [
    {
      "rank": 1,
      "vendor_name": "Vendor A",
      "score": 6.0,
      "price": 335.0,
      "payment_terms_days": 30,
      "delivery_days": 10,
      "category_winners": ["Best Price"],
      "materials": [...]
    }
  ],
  "ai_insights": {
    "primary_recommendation": "Vendor A offers the best balance of price, delivery window, and payment terms for cement and steel. Recommended as primary vendor for full PO.",
    "alternate_strategy": "Use a split award: Cement → Vendor A | Steel → Vendor B for slightly better steel price, if extended payment terms are acceptable.",
    "risk_consideration": "Vendor B has historically delayed 2 out of 7 deliveries in the last 12 months. Payment terms Net 60 may impact cashflow.",
    "project_impact": "Choosing Vendor C exclusively increases total cost by ~2.1% but offers highest reliability score and consistent on-time delivery.",
    "negotiation_tips": [
      "Leverage Vendor B's lower steel price to negotiate 5% reduction",
      "Request 15-day delivery to match Vendor C's timeline",
      "Inquire about volume discounts for bulk orders"
    ]
  },
  "metadata": {
    "total_vendors": 4,
    "analysis_date": "2025-12-10T05:51:00",
    "total_materials": 8
  }
}
```

---

## 🎯 **EXACT MAPPING TO YOUR ANGULAR PAGE**

### **Your Angular Page Has:**

```html
<div class="ai-list">
  <div class="ai-item">
    <div class="ai-label">Primary Recommendation</div>
    <!-- Display: ai_insights.primary_recommendation -->
  </div>
  
  <div class="ai-item">
    <div class="ai-label">Alternate Strategy</div>
    <!-- Display: ai_insights.alternate_strategy -->
  </div>
  
  <div class="ai-item">
    <div class="ai-label">Risk Consideration</div>
    <!-- Display: ai_insights.risk_consideration -->
  </div>
  
  <div class="ai-item">
    <div class="ai-label">Project Impact</div>
    <!-- Display: ai_insights.project_impact -->
  </div>
</div>
```

---

## 💻 **STEP-BY-STEP ANGULAR IMPLEMENTATION**

### **Step 1: Create TypeScript Interface**

**File:** `src/app/models/vendor-comparison.model.ts`

```typescript
export interface VendorRanking {
  rank: number;
  vendor_name: string;
  score: number;
  price: number;
  payment_terms_days: number;
  delivery_days: number;
  category_winners: string[];
  materials?: Material[];
}

export interface Material {
  mat_code: string;
  mat_text: string;
  price: number;
  qty: number;
  uom: string;
}

export interface AIInsights {
  primary_recommendation: string;
  alternate_strategy: string;
  risk_consideration: string;
  project_impact: string;
  negotiation_tips: string[];
}

export interface ComparisonResponse {
  rfq_no: string;
  plant_code: number;
  priority: string;
  ranking: VendorRanking[];
  ai_insights: AIInsights;
  metadata: {
    total_vendors: number;
    analysis_date: string;
    total_materials: number;
  };
}
```

---

### **Step 2: Create Vendor Comparison Service**

**File:** `src/app/services/vendor-comparison.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ComparisonResponse } from '../models/vendor-comparison.model';

@Injectable({
  providedIn: 'root'
})
export class VendorComparisonService {
  private apiUrl = 'http://localhost:8000/api/vendor-comparison';

  constructor(private http: HttpClient) {}

  /**
   * Analyze RFQ vendor quotations from database
   */
  analyzeRFQ(
    rfqNo: string, 
    plantCode: number, 
    priority: 'balanced' | 'low_price' | 'fast_delivery' | 'payment_terms' = 'balanced'
  ): Observable<ComparisonResponse> {
    return this.http.post<ComparisonResponse>(`${this.apiUrl}/analyze`, {
      rfq_no: rfqNo,
      plant_code: plantCode,
      priority: priority
    });
  }

  /**
   * Get list of recent RFQs
   */
  getRecentRFQs(plantCode: number, limit: number = 10): Observable<any> {
    return this.http.get(`${this.apiUrl}/../rfq/list?plant_code=${plantCode}&limit=${limit}`);
  }
}
```

---

### **Step 3: Update Your Quotation Analysis Component**

**File:** `src/app/components/quotation-analysis/quotation-analysis.component.ts`

```typescript
import { Component, OnInit } from '@angular/core';
import { VendorComparisonService } from '../../services/vendor-comparison.service';
import { ComparisonResponse, VendorRanking, AIInsights } from '../../models/vendor-comparison.model';

@Component({
  selector: 'app-quotation-analysis',
  templateUrl: './quotation-analysis.component.html',
  styleUrls: ['./quotation-analysis.component.css']
})
export class QuotationAnalysisComponent implements OnInit {
  // RFQ Details
  rfqNo: string = 'RFQ-2024-1001';
  plantCode: number = 1100;
  priority: string = 'balanced';
  
  // Results
  vendorRanking: VendorRanking[] = [];
  aiInsights: AIInsights | null = null;
  topVendor: VendorRanking | null = null;
  
  // UI State
  loading: boolean = false;
  error: string = '';
  analysisReady: boolean = false;

  constructor(private vendorService: VendorComparisonService) {}

  ngOnInit() {
    // Optionally auto-load analysis on page load
    // this.runAIAnalysis();
  }

  /**
   * Run AI vendor analysis
   */
  runAIAnalysis() {
    this.loading = true;
    this.error = '';
    this.analysisReady = false;
    
    console.log('🤖 Running AI analysis...', {
      rfq: this.rfqNo,
      plant: this.plantCode,
      priority: this.priority
    });
    
    this.vendorService.analyzeRFQ(this.rfqNo, this.plantCode, this.priority as any)
      .subscribe({
        next: (response: ComparisonResponse) => {
          console.log('✅ Analysis complete:', response);
          
          // Update vendor ranking
          this.vendorRanking = response.ranking;
          this.topVendor = response.ranking[0];
          
          // Update AI insights
          this.aiInsights = response.ai_insights;
          
          // Update UI state
          this.loading = false;
          this.analysisReady = true;
          
          // Show success message
          this.showSuccessToast('AI analysis completed successfully!');
        },
        error: (error) => {
          console.error('❌ Analysis failed:', error);
          this.error = error.error?.detail || 'Analysis failed. Please try again.';
          this.loading = false;
          this.analysisReady = false;
          
          // Show error message
          this.showErrorToast(this.error);
        }
      });
  }

  /**
   * Re-run analysis with different priority
   */
  changePriority(newPriority: string) {
    this.priority = newPriority;
    this.runAIAnalysis();
  }

  /**
   * Helper: Show success toast
   */
  private showSuccessToast(message: string) {
    // Implement your toast notification
    alert(message);
  }

  /**
   * Helper: Show error toast
   */
  private showErrorToast(message: string) {
    // Implement your toast notification
    alert(message);
  }
}
```

---

### **Step 4: Update Your HTML Template**

**File:** `src/app/components/quotation-analysis/quotation-analysis.component.html`

```html
<!-- Add this button to trigger AI analysis -->
<div class="header-right">
  <button 
    class="pill pill-cta" 
    (click)="runAIAnalysis()" 
    [disabled]="loading">
    <span *ngIf="!loading">🤖 AI Vendor Analysis</span>
    <span *ngIf="loading">🔄 Analyzing...</span>
  </button>
  
  <span *ngIf="analysisReady" class="badge-success">
    Recommendation Ready
  </span>
</div>

<!-- Vendor Ranking Section -->
<div class="card" *ngIf="vendorRanking.length > 0">
  <div class="card-header">
    <div>
      <div class="card-title">
        <span class="card-dot"></span> AI Vendor Ranking
      </div>
      <div class="card-sub">Scored on Price, Delivery, Terms, History</div>
    </div>
    <span class="badge-success">Recommendation Ready</span>
  </div>
  <ul class="vendor-ranking-list">
    <li *ngFor="let vendor of vendorRanking">
      <span class="vendor-ranking-name">
        <span class="star" *ngIf="vendor.rank <= 2">★</span> 
        {{ vendor.vendor_name }}
      </span>
      <span [ngClass]="vendor.rank === 1 ? 'badge-chip' : 'badge'">
        Score: {{ vendor.score }} / 100
        <span *ngIf="vendor.category_winners.length > 0">
          · {{ vendor.category_winners.join(', ') }}
        </span>
      </span>
    </li>
  </ul>
</div>

<!-- AI Insights Section (YOUR EXISTING CARD) -->
<div class="card" *ngIf="aiInsights">
  <div class="card-header">
    <div>
      <div class="card-title">
        <span class="card-dot"></span> AI Insights
      </div>
      <div class="card-sub">How Compreo evaluates this RFQ</div>
    </div>
    <span class="badge">AI View</span>
  </div>
  
  <div class="ai-list">
    <!-- Primary Recommendation -->
    <div class="ai-item">
      <div class="ai-label">Primary Recommendation</div>
      {{ aiInsights.primary_recommendation }}
    </div>
    
    <!-- Alternate Strategy -->
    <div class="ai-item">
      <div class="ai-label">Alternate Strategy</div>
      {{ aiInsights.alternate_strategy }}
    </div>
    
    <!-- Risk Consideration -->
    <div class="ai-item">
      <div class="ai-label">Risk Consideration</div>
      {{ aiInsights.risk_consideration }}
    </div>
    
    <!-- Project Impact -->
    <div class="ai-item">
      <div class="ai-label">Project Impact</div>
      {{ aiInsights.project_impact }}
    </div>
    
    <!-- Optional: Negotiation Tips -->
    <div class="ai-item" *ngIf="aiInsights.negotiation_tips.length > 0">
      <div class="ai-label">Negotiation Tips</div>
      <ul>
        <li *ngFor="let tip of aiInsights.negotiation_tips">{{ tip }}</li>
      </ul>
    </div>
  </div>
</div>

<!-- Loading State -->
<div class="card" *ngIf="loading">
  <div style="text-align: center; padding: 40px;">
    <div class="spinner"></div>
    <p>🤖 Analyzing vendor quotations...</p>
    <p class="card-sub">Fetching data, ranking vendors, generating AI insights</p>
  </div>
</div>

<!-- Error State -->
<div class="card" *ngIf="error && !loading">
  <div style="color: #ef4444; padding: 20px;">
    <strong>❌ Analysis Failed</strong>
    <p>{{ error }}</p>
    <button class="btn" (click)="runAIAnalysis()">Retry Analysis</button>
  </div>
</div>
```

---

## 🔧 **OPTIONAL: Add Priority Selector**

```html
<!-- Add dropdown to change priority -->
<div class="priority-selector">
  <label>Analysis Priority:</label>
  <select [(ngModel)]="priority" (change)="changePriority(priority)">
    <option value="balanced">Balanced</option>
    <option value="low_price">Low Price</option>
    <option value="fast_delivery">Fast Delivery</option>
    <option value="payment_terms">Payment Terms</option>
  </select>
</div>
```

---

## ✅ **COMPLETE WORKFLOW**

1. **User clicks "AI Vendor Analysis" button**
2. **Angular calls FastAPI:** `POST /api/vendor-comparison/analyze`
3. **FastAPI:**
   - Fetches vendor quotations from SQL Server
   - Ranks vendors based on priority
   - Generates 4 AI insight sections using LLM
   - Returns JSON response
4. **Angular receives response** and displays:
   - Vendor ranking table
   - Primary Recommendation
   - Alternate Strategy
   - Risk Consideration
   - Project Impact

---

## 🎯 **TESTING**

### **Test in Browser Console:**

```javascript
// After clicking "AI Vendor Analysis" button
// Check console for:
console.log('✅ Analysis complete:', response);

// Response should have:
response.ai_insights.primary_recommendation
response.ai_insights.alternate_strategy
response.ai_insights.risk_consideration
response.ai_insights.project_impact
```

---

## 🚀 **YOU'RE DONE!**

Your Angular page will now display **4 detailed AI sections** exactly matching your mockup!

**Next:** Just add your OpenRouter API key to `.env` and the AI will generate intelligent recommendations!
