"""
API Models - Request and Response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class PriorityType(str, Enum):
    """Priority options for vendor comparison"""
    BALANCED = "balanced"
    LOW_PRICE = "low_price"
    FAST_DELIVERY = "fast_delivery"
    PAYMENT_TERMS = "payment_terms"


class AnalyzeRFQRequest(BaseModel):
    """Request model for analyzing RFQ vendor quotations"""
    rfq_no: str = Field(..., example="RFQ-2024-1001", description="RFQ number")
    plant_code: int = Field(..., example=1100, description="Plant code")
    priority: PriorityType = Field(default=PriorityType.BALANCED, description="Ranking priority")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rfq_no": "RFQ-2024-1001",
                "plant_code": 1100,
                "priority": "balanced"
            }
        }


class VendorParameters(BaseModel):
    """Vendor parameters for comparison"""
    price: float = Field(..., description="Price per unit in INR")
    payment_terms_days: int = Field(..., description="Payment terms in days")
    delivery_days: int = Field(..., description="Delivery time in days")


class ManualVendorEntry(BaseModel):
    """Manual vendor entry for comparison"""
    vendor_name: str = Field(..., example="ABC Industries")
    price: float = Field(..., example=150.0)
    payment_terms_days: int = Field(..., example=30)
    delivery_days: int = Field(..., example=7)


class AnalyzeManualRequest(BaseModel):
    """Request model for manual vendor entry"""
    vendors: List[ManualVendorEntry] = Field(..., min_items=2)
    priority: PriorityType = Field(default=PriorityType.BALANCED)
    
    class Config:
        json_schema_extra = {
            "example": {
                "vendors": [
                    {"vendor_name": "Alpha Traders", "price": 150, "payment_terms_days": 30, "delivery_days": 7},
                    {"vendor_name": "Beta Supplies", "price": 135, "payment_terms_days": 60, "delivery_days": 10}
                ],
                "priority": "balanced"
            }
        }


class MaterialInfo(BaseModel):
    """Material information in quotation"""
    mat_code: str
    mat_text: str
    price: float
    qty: float
    uom: str


class VendorContact(BaseModel):
    """Vendor contact information"""
    email: Optional[str] = ""
    person: Optional[str] = ""
    phone: Optional[str] = ""


class RankingResult(BaseModel):
    """Vendor ranking result"""
    rank: int = Field(..., description="Vendor rank (1 = best)")
    vendor_name: str
    vendor_no: str = Field(..., description="Vendor number/code")  # ADD THIS!
    score: float = Field(..., description="Weighted ranking score (lower = better)")
    display_score: int = Field(..., description="Display score 20-100 (higher = better)")  # NEW!
    price: float = Field(..., description="Price in INR")
    payment_terms_days: int = Field(..., description="Payment terms in days")
    delivery_days: int = Field(..., description="Delivery days")
    category_winners: List[str] = Field(default_factory=list, description="Categories where vendor wins")
    materials: Optional[List[MaterialInfo]] = Field(default_factory=list)
    contact: Optional[VendorContact] = None

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "vendor_name": "ABC Industries",
                "score": 4.5,
                "display_score": 100,  # NEW!
                "price": 850.00,
                "payment_terms_days": 30,
                "delivery_days": 7,
                "category_winners": ["Best Price", "Fastest Delivery"],
                "materials": [],
                "contact": {
                    "email": "contact@abc.com",
                    "person": "John Doe",
                    "phone": "+91-9876543210"
                }
            }
        }


class AIInsights(BaseModel):
    """AI-generated insights and recommendations"""
    primary_recommendation: str = Field(..., description="Main vendor recommendation with reasoning")
    alternate_strategy: str = Field(..., description="Alternative procurement strategy or split award options")
    risk_consideration: str = Field(..., description="Risk factors and concerns to be aware of")
    project_impact: str = Field(..., description="Impact on project timeline, budget, and delivery")
    line_item_insights: Optional[str] = Field(default="", description="Material-level analysis insights")
    split_award_recommendation: Optional[str] = Field(default="", description="Split-award strategy recommendation")
    negotiation_tips: List[str] = Field(default_factory=list, description="Specific negotiation tactics")


class VendorQuoteForMaterial(BaseModel):
    """Single vendor's quote for a material"""
    vendor_name: str
    vendor_no: str = "" 
    price: float
    payment_terms_days: int
    delivery_days: int
    total_value: float
    rank_for_this_material: int
    rank_score: float = Field(..., description="Ranking score for this material")
    is_best_price: bool
    is_best_payment: bool
    is_best_delivery: bool
    price_difference_from_best: float
    savings_vs_worst: float
    vendor_email: str = ""
    vendor_contact_person: str = ""
    vendor_contact_phone: str = ""


class RecommendedVendorForMaterial(BaseModel):
    """Recommended vendor for a specific material"""
    vendor_name: str
    vendor_no: str = ""  
    price: float
    payment_terms_days: int
    delivery_days: int
    total_value: float
    score: float
    display_score: int = Field(default=100, description="Display score 20-100 (higher = better)")  # NEW!
    reason: str
    savings: float
    savings_percentage: float
    alternative: Optional[Dict] = None


class MaterialLineItem(BaseModel):
    """Line-item analysis for a single material"""
    mat_code: str
    mat_text: str
    qty: float
    uom: str
    vendor_quotes: List[VendorQuoteForMaterial]
    recommended_vendor: RecommendedVendorForMaterial


class VendorAllocation(BaseModel):
    """Vendor allocation in split-award strategy"""
    vendor_name: str
    materials: List[str]  
    material_codes: List[str]
    total_value: float
    material_count: int
    percentage_of_order: float


class SplitAwardStrategy(BaseModel):
    """Split-award strategy recommendation"""
    is_recommended: bool
    total_cost_split: float
    total_cost_single_vendor: float
    total_savings: float
    savings_percentage: float
    vendor_count: int
    vendor_allocation: List[VendorAllocation]
    comparison_vs_single_vendor: Optional[Dict] = None


class LineItemAnalysis(BaseModel):
    """Complete line-item level analysis"""
    materials: List[MaterialLineItem]
    split_award_strategy: SplitAwardStrategy


class ComparisonResponse(BaseModel):
    """Response model for vendor comparison"""
    rfq_no: Optional[str] = None
    plant_code: Optional[int] = None
    priority: str
    ranking: List[RankingResult]
    line_item_analysis: Optional[LineItemAnalysis] = None
    ai_insights: AIInsights
    metadata: Dict = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "rfq_no": "RFQ-2024-1001",
                "plant_code": 1100,
                "priority": "balanced",
                "ranking": [
                    {
                        "rank": 1,
                        "vendor_name": "Beta Supplies",
                        "score": 6,
                        "display_score": 100,
                        "price": 135.0,
                        "payment_terms_days": 60,
                        "delivery_days": 10,
                        "category_winners": ["Best Payment Terms"],
                        "materials": []
                    }
                ],
                "ai_insights": {
                    "primary_recommendation": "Vendor A offers the best balance of price, delivery window, and payment terms...",
                    "alternate_strategy": "Consider split award: Cement → Vendor A, Steel → Vendor B for better pricing...",
                    "risk_consideration": "Vendor B has historically delayed 2 out of 7 deliveries in the last 12 months...",
                    "project_impact": "Choosing Vendor C exclusively increases total cost by ~2.1% but offers highest reliability...",
                    "negotiation_tips": ["Request volume discounts", "Negotiate faster delivery"]
                },
                "metadata": {
                    "total_vendors": 4,
                    "analysis_date": "2024-12-09"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str
    status_code: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Database Error",
                "detail": "Failed to connect to SQL Server",
                "status_code": 500
            }
        }