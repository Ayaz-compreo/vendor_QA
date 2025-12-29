"""
Enhanced AI Engine - Generates structured insights and recommendations
"""
from typing import List, Dict
import re
from models import VendorAnalysis, AIInsights, StructuredRecommendation, StructuredInsight


class AIInsightsEngineEnhanced:
    """Generate structured AI insights with recommendations"""
    
    def __init__(self):
        """Initialize AI engine"""
        from dotenv import load_dotenv
        from openai import OpenAI
        import os
        
        load_dotenv()
        
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("LLM_MODEL", "google/gemma-3-27b-it:free")
        
        print(f"🔍 AI Engine Init: Key length = {len(self.api_key) if self.api_key else 0}")
        
        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                print("✅ OpenAI client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize: {e}")
                self.client = None
        else:
            self.client = None
            print("⚠️ No API key, using default insights")
    
    def generate_structured_analysis(
        self, 
        vendor_analysis: List[VendorAnalysis], 
        priority: str, 
        line_item_data: Dict = None
    ) -> tuple[List[StructuredRecommendation], List[StructuredInsight], AIInsights]:
        """
        Generate structured recommendations, insights, and legacy AI insights
        
        Returns:
            Tuple of (recommendations, structured_insights, ai_insights)
        """
        if not vendor_analysis:
            return ([], [], self._default_ai_insights())
        
        winner = vendor_analysis[0]
        second = vendor_analysis[1] if len(vendor_analysis) > 1 else None
        
        # Generate structured recommendations
        recommendations = self._generate_recommendations(vendor_analysis, priority)
        
        # Generate structured insights
        structured_insights = self._generate_structured_insights(
            vendor_analysis, 
            priority, 
            line_item_data
        )
        
        # Generate legacy AI insights (for backward compatibility)
        ai_insights = self._generate_legacy_ai_insights(
            vendor_analysis, 
            priority, 
            line_item_data
        )
        
        return (recommendations, structured_insights, ai_insights)
    
    def _generate_recommendations(
        self, 
        vendor_analysis: List[VendorAnalysis], 
        priority: str
    ) -> List[StructuredRecommendation]:
        """Generate structured recommendations"""
        recommendations = []
        
        winner = vendor_analysis[0]
        second = vendor_analysis[1] if len(vendor_analysis) > 1 else None
        
        # PRIMARY RECOMMENDATION
        primary_benefits = []
        
        # Identify winner's strengths
        for dim_score in winner.dimension_scores:
            if dim_score.score and dim_score.score >= 8.0:
                primary_benefits.append(f"{dim_score.dimension_code}: {dim_score.evidence_text}")
            elif dim_score.bool_value:
                primary_benefits.append(f"{dim_score.dimension_code}: {dim_score.evidence_text}")
        
        # Build negotiation tips
        negotiation_tips = []
        if second:
            for i, dim in enumerate(winner.dimension_scores):
                if dim.score and second.dimension_scores[i].score:
                    if second.dimension_scores[i].score > dim.score + 1:
                        negotiation_tips.append({
                            "dimension": dim.dimension_code,
                            "tip": f"Leverage {second.vendor_name}'s better {dim.dimension_code.lower()}",
                            "target": "Negotiate improvement"
                        })
        
        primary_rec = StructuredRecommendation(
            recommendation_type="PRIMARY",
            vendor_no=winner.vendor_no,
            vendor_name=winner.vendor_name,
            summary_text=f"Award contract to {winner.vendor_name} for optimal balance of {priority} priority. "
                        f"Overall score: {winner.overall_score}/10 with quoted amount of ₹{winner.quoted_amount:,.0f}.",
            key_benefits=primary_benefits[:3],  # Top 3 benefits
            negotiation_tips_json={"tips": negotiation_tips} if negotiation_tips else None
        )
        recommendations.append(primary_rec)
        
        # ALTERNATE RECOMMENDATION (if second vendor exists)
        if second:
            alternate_benefits = []
            for dim_score in second.dimension_scores:
                if dim_score.score and dim_score.score >= 8.0:
                    alternate_benefits.append(f"{dim_score.dimension_code}: {dim_score.evidence_text}")
            
            alternate_rec = StructuredRecommendation(
                recommendation_type="ALTERNATE",
                vendor_no=second.vendor_no,
                vendor_name=second.vendor_name,
                summary_text=f"If {priority} is not critical, consider {second.vendor_name}. "
                            f"Overall score: {second.overall_score}/10 with quoted amount of ₹{second.quoted_amount:,.0f}.",
                key_benefits=alternate_benefits[:3]
            )
            recommendations.append(alternate_rec)
        
        return recommendations
    
    def _generate_structured_insights(
        self, 
        vendor_analysis: List[VendorAnalysis], 
        priority: str, 
        line_item_data: Dict = None
    ) -> List[StructuredInsight]:
        """Generate structured insights array"""
        insights = []
        order = 1
        
        winner = vendor_analysis[0]
        second = vendor_analysis[1] if len(vendor_analysis) > 1 else None
        
        # PRIMARY RECOMMENDATION INSIGHT
        primary_text = f"{winner.vendor_name} is recommended as primary vendor. "
        primary_text += f"Overall score: {winner.overall_score}/10. "
        primary_text += f"Quote amount: ₹{winner.quoted_amount:,.0f}. "
        primary_text += f"Key strengths: {', '.join([w.category_label for w in winner.category_winners])}."
        
        insights.append(StructuredInsight(
            insight_type="PRIMARY_REC",
            insight_title="Primary Recommendation",
            insight_text=primary_text,
            insight_order=order
        ))
        order += 1
        
        # ALTERNATE STRATEGY INSIGHT
        if second:
            cost_diff = ((winner.quoted_amount - second.quoted_amount) / second.quoted_amount * 100)
            alternate_text = f"Alternate option: {second.vendor_name} with {second.overall_score}/10 score. "
            if cost_diff > 0:
                alternate_text += f"Offers {abs(cost_diff):.1f}% cost savings at ₹{second.quoted_amount:,.0f}. "
            alternate_text += f"Consider for: {', '.join([w.category_label for w in second.category_winners])}."
            
            insights.append(StructuredInsight(
                insight_type="ALTERNATE",
                insight_title="Alternate Strategy",
                insight_text=alternate_text,
                insight_order=order
            ))
            order += 1
        
        # NEGOTIATION TIPS INSIGHT
        negotiation_tips_list = []
        if second:
            # Price negotiation
            if winner.price > second.price:
                price_diff_pct = ((winner.price - second.price) / winner.price * 100)
                negotiation_tips_list.append({
                    "tip": f"Mention {second.vendor_name}'s lower price (₹{second.price:.0f})",
                    "leverage": f"{price_diff_pct:.1f}% price difference",
                    "target_savings": f"₹{(winner.quoted_amount - second.quoted_amount):,.0f}"
                })
            
            # Payment terms
            if winner.payment_terms_days < second.payment_terms_days:
                negotiation_tips_list.append({
                    "tip": f"Request {second.payment_terms_days}-day credit terms",
                    "leverage": f"Matching {second.vendor_name}'s offer",
                    "target_savings": "Improved cash flow"
                })
        
        negotiation_tips_list.append({
            "tip": "Inquire about volume discounts",
            "leverage": "Bulk order commitment",
            "target_savings": "5-10% additional savings"
        })
        
        negotiation_text = "\n".join([f"• {tip['tip']}: {tip.get('leverage', '')}" for tip in negotiation_tips_list])
        
        insights.append(StructuredInsight(
            insight_type="NEGOTIATION",
            insight_title="Negotiation Tips",
            insight_text=negotiation_text,
            insight_order=order,
            insight_json={"tips": negotiation_tips_list}
        ))
        order += 1
        
        # RISK CONSIDERATIONS INSIGHT
        risks = []
        
        # Check for low dimension scores
        for dim in winner.dimension_scores:
            if dim.score and dim.score < 6.0:
                risks.append({
                    "risk": f"Low {dim.dimension_code} score ({dim.score}/10)",
                    "severity": "MEDIUM" if dim.score >= 4.0 else "HIGH",
                    "mitigation": f"Monitor {dim.dimension_code.lower()} performance closely"
                })
        
        # Single source risk
        if len(vendor_analysis) <= 2:
            risks.append({
                "risk": "Limited vendor pool (single-source dependency)",
                "severity": "HIGH",
                "mitigation": "Qualify backup suppliers for future RFQs"
            })
        
        # Payment terms risk
        if winner.payment_terms_days == 0:
            risks.append({
                "risk": "Advance payment impacts cash flow",
                "severity": "MEDIUM",
                "mitigation": "Negotiate for at least 15-day credit terms"
            })
        
        risk_text = "\n".join([f"• {r['risk']} (Severity: {r['severity']})" for r in risks])
        
        insights.append(StructuredInsight(
            insight_type="RISK",
            insight_title="Risk Considerations",
            insight_text=risk_text,
            insight_order=order,
            insight_json={"risks": risks}
        ))
        order += 1
        
        # PROJECT IMPACT INSIGHT
        if second:
            cost_impact = ((winner.quoted_amount - second.quoted_amount) / second.quoted_amount * 100)
            impact_text = f"Choosing {winner.vendor_name} "
            if cost_impact > 0:
                impact_text += f"increases cost by {abs(cost_impact):.1f}% (₹{abs(winner.quoted_amount - second.quoted_amount):,.0f}) "
                impact_text += f"but provides better overall value with {winner.overall_score}/10 score."
            else:
                impact_text += f"reduces cost by {abs(cost_impact):.1f}% while maintaining quality."
            
            insights.append(StructuredInsight(
                insight_type="IMPACT",
                insight_title="Project Impact",
                insight_text=impact_text,
                insight_order=order
            ))
            order += 1
        
        # LINE ITEM INSIGHTS
        if line_item_data and line_item_data.get('materials'):
            for material in line_item_data['materials']:
                mat_code = material.get('mat_code', '')
                recommended = material.get('recommended_vendor', {})
                
                line_item_text = f"Material {mat_code}: {recommended.get('vendor_name', '')} recommended. "
                line_item_text += f"Price: ₹{recommended.get('price', 0):.0f}, "
                line_item_text += f"Savings: ₹{recommended.get('savings', 0):,.0f}."
                
                insights.append(StructuredInsight(
                    insight_type="LINE_ITEM",
                    insight_title=f"Material {mat_code} Analysis",
                    insight_text=line_item_text,
                    insight_order=order,
                    material_code=mat_code
                ))
                order += 1
        
        return insights
    
    def _generate_legacy_ai_insights(
        self, 
        vendor_analysis: List[VendorAnalysis], 
        priority: str, 
        line_item_data: Dict = None
    ) -> AIInsights:
        """Generate legacy AI insights using LLM for backward compatibility"""
        if not self.client:
            return self._default_ai_insights()
        
        winner = vendor_analysis[0]
        second = vendor_analysis[1] if len(vendor_analysis) > 1 else None
        
        # Prepare vendor summary for LLM
        vendors_summary = self._build_vendors_summary(vendor_analysis)
        
        # Generate PRIMARY RECOMMENDATION using LLM
        primary_rec = self._generate_primary_recommendation_llm(vendors_summary, winner, priority)
        
        # Generate ALTERNATE STRATEGY using LLM
        alternate = self._generate_alternate_strategy_llm(vendors_summary, winner, second, priority)
        
        # Generate RISK CONSIDERATION using LLM
        risk = self._generate_risk_consideration_llm(vendors_summary, winner, vendor_analysis)
        
        # Generate PROJECT IMPACT using LLM
        impact = self._generate_project_impact_llm(vendors_summary, winner, second)
        
        # Generate NEGOTIATION TIPS using LLM
        tips = self._generate_negotiation_tips_llm(vendors_summary, winner, second)
        
        # Generate LINE ITEM INSIGHTS using LLM
        line_item_insights = ""
        if line_item_data and line_item_data.get('materials'):
            line_item_insights = self._generate_line_item_insights_llm(line_item_data)
        
        return AIInsights(
            primary_recommendation=primary_rec,
            alternate_strategy=alternate,
            risk_consideration=risk,
            project_impact=impact,
            line_item_insights=line_item_insights,
            split_award_recommendation="",
            negotiation_tips=tips
        )
    
    def _build_vendors_summary(self, vendor_analysis: List[VendorAnalysis]) -> str:
        """Build comprehensive vendor summary for LLM context"""
        summary = "VENDOR ANALYSIS:\n\n"
        
        for vendor in vendor_analysis:
            summary += f"Rank #{vendor.rank}: {vendor.vendor_name} (Vendor No: {vendor.vendor_no})\n"
            summary += f"  Overall Score: {vendor.overall_score}/10\n"
            summary += f"  Quoted Amount: ₹{vendor.quoted_amount:,.0f}\n"
            summary += f"  Average Price: ₹{vendor.price:.0f}/unit\n"
            summary += f"  Payment Terms: {vendor.payment_terms_days} days\n"
            summary += f"  Delivery: {vendor.delivery_days} days\n"
            summary += f"  Category Winners: {', '.join([w.category_label for w in vendor.category_winners])}\n"
            
            summary += f"  Dimension Scores:\n"
            for dim in vendor.dimension_scores:
                if dim.score is not None:
                    summary += f"    - {dim.dimension_code}: {dim.score}/10 - {dim.evidence_text}\n"
                else:
                    summary += f"    - {dim.dimension_code}: {dim.bool_value} - {dim.evidence_text}\n"
            summary += "\n"
        
        return summary
    
    def _safe_llm_call(self, prompt: str, max_tokens: int, fallback: str) -> str:
        """Safely call LLM with error handling and markdown cleaning"""
        try:
            print(f"🚀 Calling OpenRouter API with model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            
            if response and response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if message and hasattr(message, 'content') and message.content:
                    return self._clean_markdown(message.content.strip())
            
            print("⚠️ Empty LLM response, using fallback")
            return fallback
            
        except Exception as e:
            print(f"❌ LLM call error: {e}")
            return fallback
    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from LLM responses"""
        import re
        
        # Remove bold (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # Remove italic (*text* or _text_)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # Remove headers (##, ###)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove standalone asterisks (NEW!)
        text = re.sub(r'^\*+\s*', '', text)  # Leading
        text = re.sub(r'\s*\*+$', '', text)  # Trailing
        text = re.sub(r'\n\*+\s*\n', '\n\n', text)  # Asterisks on their own line
        
        # Clean whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
    '''def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from LLM responses"""
        import re
        # Remove bold (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        # Remove italic (*text* or _text_)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        # Remove headers (##, ###)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Clean whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()'''
    
    def _generate_primary_recommendation_llm(self, vendors_summary: str, winner: VendorAnalysis, priority: str) -> str:
        """Generate primary recommendation using LLM"""
        payment_str = "advance payment" if winner.payment_terms_days == 0 else f"{winner.payment_terms_days} days credit"
        
        prompt = f"""You are a procurement analyst. Based on this vendor analysis, provide a PRIMARY RECOMMENDATION.

{vendors_summary}

USER PRIORITY: {priority}
RECOMMENDED VENDOR: {winner.vendor_name} (Rank #1)

Write a concise primary recommendation (max 120 words) that:
1. States why {winner.vendor_name} is the best choice
2. Highlights their key strengths (overall score: {winner.overall_score}/10, price: ₹{winner.price:.0f}, payment: {payment_str}, delivery: {winner.delivery_days} days)
3. Explains how they meet the {priority} priority
4. Recommends issuing Purchase Order to them

Be direct and confident. Start with: "{winner.vendor_name} is recommended..."
NO MARKDOWN FORMATTING. Plain text only."""

        fallback = f"{winner.vendor_name} is recommended as primary vendor with overall score {winner.overall_score}/10."
        return self._safe_llm_call(prompt, max_tokens=250, fallback=fallback)
    
    def _generate_alternate_strategy_llm(self, vendors_summary: str, winner: VendorAnalysis, second: VendorAnalysis, priority: str) -> str:
        """Generate alternate strategy using LLM"""
        if not second:
            return "Single vendor option. Consider inviting more vendors for future RFQs to increase competition."
        
        prompt = f"""You are a procurement analyst. Suggest an ALTERNATE STRATEGY based on this analysis.

{vendors_summary}

USER PRIORITY: {priority}
PRIMARY CHOICE: {winner.vendor_name}
ALTERNATE OPTION: {second.vendor_name}

Write a concise alternate strategy (max 100 words) that:
1. Explains when/why to consider {second.vendor_name}
2. Highlights their unique strengths
3. Suggests split-award or backup supplier strategy
4. Mentions cost vs quality tradeoffs

Be practical and strategic.
NO MARKDOWN FORMATTING. Plain text only."""

        fallback = f"Consider {second.vendor_name} as backup supplier (score: {second.overall_score}/10)."
        return self._safe_llm_call(prompt, max_tokens=200, fallback=fallback)
    
    def _generate_risk_consideration_llm(self, vendors_summary: str, winner: VendorAnalysis, all_vendors: List[VendorAnalysis]) -> str:
        """Generate risk consideration using LLM"""
        risk_factors = []
        
        # Identify risks from dimension scores
        for dim in winner.dimension_scores:
            if dim.score and dim.score < 6.0:
                risk_factors.append(f"{dim.dimension_code} score is low ({dim.score}/10)")
        
        if winner.payment_terms_days == 0:
            risk_factors.append("Advance payment required")
        
        if len(all_vendors) <= 2:
            risk_factors.append("Limited vendor pool (single-source dependency)")
        
        risks_text = ", ".join(risk_factors) if risk_factors else "Standard risks"
        
        prompt = f"""You are a procurement risk analyst. Identify KEY RISKS for this vendor selection.

{vendors_summary}

RECOMMENDED VENDOR: {winner.vendor_name}
IDENTIFIED RISK FACTORS: {risks_text}

Write a concise risk assessment (max 100 words) that:
1. Lists 2-3 critical risks
2. Explains potential impact of each risk
3. Suggests mitigation strategies
4. Be realistic but not alarmist

Focus on actionable insights.
NO MARKDOWN FORMATTING. Plain text only."""

        fallback = f"Primary risks: {risks_text}. Monitor performance and maintain backup suppliers."
        return self._safe_llm_call(prompt, max_tokens=200, fallback=fallback)
    
    def _generate_project_impact_llm(self, vendors_summary: str, winner: VendorAnalysis, second: VendorAnalysis) -> str:
        """Generate project impact using LLM"""
        if not second:
            prompt = f"""You are a procurement analyst. Explain the PROJECT IMPACT of this vendor selection.

VENDOR: {winner.vendor_name}
Overall Score: {winner.overall_score}/10
Quoted Amount: ₹{winner.quoted_amount:,.0f}
Delivery: {winner.delivery_days} days

Write a brief impact statement (max 80 words) covering:
1. How this choice affects project timeline
2. Budget implications
3. Quality/reliability expectations

Be concise and factual.
NO MARKDOWN FORMATTING. Plain text only."""
        else:
            cost_diff = ((winner.quoted_amount - second.quoted_amount) / second.quoted_amount * 100)
            
            prompt = f"""You are a procurement analyst. Explain the PROJECT IMPACT of selecting {winner.vendor_name} over {second.vendor_name}.

PRIMARY CHOICE: {winner.vendor_name}
- Score: {winner.overall_score}/10
- Amount: ₹{winner.quoted_amount:,.0f}
- Delivery: {winner.delivery_days} days

ALTERNATE: {second.vendor_name}
- Score: {second.overall_score}/10
- Amount: ₹{second.quoted_amount:,.0f}
- Delivery: {second.delivery_days} days

COST DIFFERENCE: {abs(cost_diff):.1f}% {"higher" if cost_diff > 0 else "lower"}

Write a brief impact statement (max 100 words) covering:
1. Cost vs quality tradeoff
2. Timeline implications
3. Overall value justification

Be balanced and factual.
NO MARKDOWN FORMATTING. Plain text only."""

        fallback = f"Selecting {winner.vendor_name} provides balanced value with {winner.overall_score}/10 score."
        return self._safe_llm_call(prompt, max_tokens=200, fallback=fallback)
    
    def _generate_negotiation_tips_llm(self, vendors_summary: str, winner: VendorAnalysis, second: VendorAnalysis) -> List[str]:
        """Generate negotiation tips using LLM"""
        context = f"PRIMARY VENDOR: {winner.vendor_name} (₹{winner.price:.0f}/unit, {winner.payment_terms_days}d credit, {winner.delivery_days}d delivery)"
        
        if second:
            context += f"\nALTERNATE: {second.vendor_name} (₹{second.price:.0f}/unit, {second.payment_terms_days}d credit, {second.delivery_days}d delivery)"
        
        prompt = f"""You are a procurement negotiation expert. Provide 3 SPECIFIC negotiation tips.

{context}

List exactly 3 actionable negotiation tactics (one per line):
1. [First tip - be specific with numbers/percentages]
2. [Second tip - leverage competition or volume]
3. [Third tip - payment terms or delivery improvement]

Be concise. Each tip should be 10-15 words maximum.
NO MARKDOWN FORMATTING. Plain text only."""

        fallback_tips = [
            f"Leverage competitive pricing to negotiate {5}% reduction",
            "Request volume discounts for bulk orders",
            "Negotiate extended payment terms for cash flow improvement"
        ]
        
        result = self._safe_llm_call(prompt, max_tokens=150, fallback="\n".join(fallback_tips))
        
        # Parse tips from LLM response
        tips = []
        for line in result.split('\n'):
            line = line.strip()
            # Remove numbering (1., 2., etc.)
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            if line and len(line) > 10:
                tips.append(line)
        
        return tips[:3] if tips else fallback_tips
    
    def _generate_line_item_insights_llm(self, line_item_data: Dict) -> str:
        """Generate line-item insights using LLM"""
        materials_summary = "MATERIAL-LEVEL ANALYSIS:\n\n"
        
        for material in line_item_data.get('materials', []):
            mat_code = material.get('mat_code', '')
            mat_text = material.get('mat_text', '')
            recommended = material.get('recommended_vendor', {})
            
            materials_summary += f"Material: {mat_code} - {mat_text}\n"
            materials_summary += f"  Recommended: {recommended.get('vendor_name', '')} @ ₹{recommended.get('price', 0):.0f}\n"
            materials_summary += f"  Savings: ₹{recommended.get('savings', 0):,.0f} ({recommended.get('savings_percentage', 0):.1f}%)\n"
            materials_summary += f"  Quotes received: {len(material.get('vendor_quotes', []))}\n\n"
        
        prompt = f"""You are a procurement analyst. Analyze these MATERIAL-LEVEL quotations.

{materials_summary}

Provide a brief analysis (max 120 words) covering:
1. Significant price variations between materials
2. Optimization opportunities per material
3. Risk of split awards vs single vendor

Be concise and actionable.
NO MARKDOWN FORMATTING. Plain text only."""

        fallback = "Material-level analysis shows competitive pricing across line items."
        return self._safe_llm_call(prompt, max_tokens=250, fallback=fallback)
    
    def _default_ai_insights(self) -> AIInsights:
        """Default insights when no data available"""
        return AIInsights(
            primary_recommendation="Insufficient data for analysis",
            alternate_strategy="N/A",
            risk_consideration="N/A",
            project_impact="N/A",
            negotiation_tips=[]
        )