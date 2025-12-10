"""
AI Engine - Generates insights and recommendations using LLM
"""
import os
from typing import List
from openai import OpenAI
from models import RankingResult, AIInsights


class AIInsightsEngine:
    """Generate AI-powered insights using LLM"""
    
    def __init__(self):
        """Initialize AI engine with OpenRouter"""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-exp:free")
        
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.client = None
    
    def generate_insights(self, ranking: List[RankingResult], priority: str) -> AIInsights:
        """
        Generate comprehensive AI insights with 4 detailed sections
        
        Args:
            ranking: List of ranked vendors
            priority: User's priority
            
        Returns:
            AIInsights object with 4 detailed sections + negotiation tips
        """
        if not self.client:
            # Return default insights if API key not configured
            return self._default_insights(ranking, priority)
        
        try:
            # Prepare vendor summary
            vendors_summary = self._prepare_vendor_summary(ranking)
            winner = ranking[0]
            second = ranking[1] if len(ranking) > 1 else None
            
            # Generate all 4 sections using LLM
            primary_rec = self._generate_primary_recommendation(vendors_summary, winner, priority)
            alternate_strategy = self._generate_alternate_strategy(ranking, winner, second)
            risk_consideration = self._generate_risk_consideration(ranking, winner)
            project_impact = self._generate_project_impact(ranking, winner, priority)
            negotiation_tips = self._generate_negotiation_tips(ranking, priority)
            
            return AIInsights(
                primary_recommendation=primary_rec,
                alternate_strategy=alternate_strategy,
                risk_consideration=risk_consideration,
                project_impact=project_impact,
                negotiation_tips=negotiation_tips
            )
            
        except Exception as e:
            print(f"AI generation error: {str(e)}")
            return self._default_insights(ranking, priority)
    
    def _prepare_vendor_summary(self, ranking: List[RankingResult]) -> str:
        """Prepare concise vendor summary for LLM"""
        vendors_summary = []
        for rank in ranking[:4]:  # Top 4 vendors only
            payment_str = "Advance payment" if rank.payment_terms_days == 0 else f"{rank.payment_terms_days} days credit"
            categories = f" [{', '.join(rank.category_winners)}]" if rank.category_winners else ""
            vendors_summary.append(f"{rank.rank}. {rank.vendor_name}: ₹{rank.price:.0f}/unit, {payment_str}, {rank.delivery_days} days{categories}")
        return '\n'.join(vendors_summary)
    
    def _generate_primary_recommendation(self, vendors_summary: str, winner: RankingResult, priority: str) -> str:
        """Generate primary recommendation section"""
        payment_str = "advance payment" if winner.payment_terms_days == 0 else f"{winner.payment_terms_days} days credit"
        
        prompt = f"""You are a procurement analyst. Based on this vendor analysis, provide a PRIMARY RECOMMENDATION.

VENDOR RANKING:
{vendors_summary}

USER PRIORITY: {priority}
RECOMMENDED VENDOR: {winner.vendor_name}

Write a concise primary recommendation (max 100 words) that:
1. States why {winner.vendor_name} is the best choice
2. Highlights their key strengths (price: ₹{winner.price:.0f}, payment: {payment_str}, delivery: {winner.delivery_days} days)
3. Explains how they meet the {priority} priority
4. Recommends them as primary vendor for full PO

Be direct and confident. Start with: "{winner.vendor_name} offers..."
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_alternate_strategy(self, ranking: List[RankingResult], winner: RankingResult, second: RankingResult) -> str:
        """Generate alternate strategy section"""
        if not second:
            return "No alternate strategy available with single vendor."
        
        prompt = f"""You are a procurement analyst. Suggest an ALTERNATE STRATEGY for this RFQ.

TOP 2 VENDORS:
1. {winner.vendor_name}: ₹{winner.price:.0f}, {winner.payment_terms_days}d credit, {winner.delivery_days}d delivery
2. {second.vendor_name}: ₹{second.price:.0f}, {second.payment_terms_days}d credit, {second.delivery_days}d delivery

Write an alternate procurement strategy (max 80 words) that:
1. Suggests a split award if beneficial (e.g., "Material A → Vendor 1, Material B → Vendor 2")
2. Or suggests using {second.vendor_name} as backup/secondary supplier
3. Explains the advantage of this approach
4. Keeps it practical and actionable

Start with: "Use a split award:" or "Consider {second.vendor_name} as..."
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_risk_consideration(self, ranking: List[RankingResult], winner: RankingResult) -> str:
        """Generate risk consideration section"""
        payment_str = "requires advance payment" if winner.payment_terms_days == 0 else f"offers {winner.payment_terms_days} days credit"
        
        prompt = f"""You are a procurement analyst. Identify RISK CONSIDERATIONS for the recommended vendor.

RECOMMENDED VENDOR: {winner.vendor_name}
- Price: ₹{winner.price:.0f}/unit
- Payment: {payment_str}
- Delivery: {winner.delivery_days} days

Write risk considerations (max 80 words) covering:
1. Payment terms risk (if advance payment or long credit impacts cash flow)
2. Delivery timeline risk (if longer than competitors)
3. Price risk (if significantly lower, quality concerns)
4. Single-source dependency risk

Be realistic but balanced. Mention specific concerns like:
- "Payment terms Net {winner.payment_terms_days} may impact cashflow"
- "Delivery of {winner.delivery_days} days is slower than competitors"
- Historical performance concerns if relevant

Start with the most important risk.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_project_impact(self, ranking: List[RankingResult], winner: RankingResult, priority: str) -> str:
        """Generate project impact section"""
        # Calculate cost comparison
        if len(ranking) > 1:
            alt_vendor = ranking[1]
            cost_diff = ((winner.price - alt_vendor.price) / alt_vendor.price * 100)
            comparison = f"{winner.vendor_name} vs {alt_vendor.vendor_name}"
        else:
            cost_diff = 0
            comparison = "single vendor"
        
        prompt = f"""You are a project analyst. Explain the PROJECT IMPACT of choosing the recommended vendor.

RECOMMENDED: {winner.vendor_name} (₹{winner.price:.0f}, {winner.delivery_days}d delivery, {winner.payment_terms_days}d credit)
COMPARISON: {comparison} (cost difference: {cost_diff:+.1f}%)
PRIORITY: {priority}

Write project impact analysis (max 80 words) covering:
1. Cost impact on project budget (mention {cost_diff:+.1f}% if significant)
2. Schedule impact (delivery timeline effect)
3. Quality/reliability considerations
4. Overall project outcome

Be specific with percentages and timelines. Example:
"Choosing {winner.vendor_name} {'increases' if cost_diff > 0 else 'reduces'} total cost by ~{abs(cost_diff):.1f}% but..."

Start with "Choosing {winner.vendor_name}..."
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_negotiation_tips(self, ranking: List[RankingResult], priority: str) -> List[str]:
        """Generate negotiation tips based on ranking"""
        tips = []
        
        if len(ranking) < 2:
            return ["Consider requesting quotes from additional vendors"]
        
        winner = ranking[0]
        second = ranking[1]
        
        # Price negotiation
        if winner.price > second.price:
            price_diff = winner.price - second.price
            price_diff_pct = (price_diff / winner.price) * 100
            tips.append(f"Mention {second.vendor_name}'s lower price (₹{second.price:.0f}) to negotiate {price_diff_pct:.1f}% reduction")
        
        # Payment terms
        if winner.payment_terms_days < second.payment_terms_days:
            tips.append(f"Request {second.payment_terms_days} days credit matching {second.vendor_name}'s terms")
        
        # Delivery
        if winner.delivery_days > second.delivery_days:
            tips.append(f"Ask for {second.delivery_days}-day delivery to match {second.vendor_name}'s timeline")
        
        # Volume discount
        tips.append("Inquire about volume discounts for bulk orders or long-term contracts")
        
        # Only return top 3 tips
        return tips[:3]
    
    def _default_insights(self, ranking: List[RankingResult], priority: str) -> AIInsights:
        """Generate default insights when AI is not available"""
        if not ranking:
            return AIInsights(
                primary_recommendation="No vendors to compare",
                alternate_strategy="Insufficient data for alternate strategy",
                risk_consideration="No risk analysis available",
                project_impact="No project impact data",
                negotiation_tips=[]
            )
        
        winner = ranking[0]
        second = ranking[1] if len(ranking) > 1 else None
        
        # Primary Recommendation
        categories = ', '.join(winner.category_winners) if winner.category_winners else 'balanced performance'
        payment_str = "advance payment" if winner.payment_terms_days == 0 else f"{winner.payment_terms_days} days credit"
        
        primary_rec = f"""{winner.vendor_name} offers the best balance of price, delivery window, and payment terms for this procurement. With a competitive price of ₹{winner.price:.0f}/unit, {payment_str}, and {winner.delivery_days}-day delivery, they provide {categories}. Recommended as primary vendor for full PO based on {priority} priority."""
        
        # Alternate Strategy
        if second:
            alt_strategy = f"""Consider a split award strategy: Use {winner.vendor_name} as primary supplier for the majority of the order, with {second.vendor_name} (₹{second.price:.0f}, {second.payment_terms_days}d credit) as secondary supplier to maintain competitive pressure and supply chain resilience. This approach provides backup options if primary vendor faces capacity constraints."""
        else:
            alt_strategy = "No alternate strategy available. Consider inviting additional vendors for future RFQs to ensure competitive pricing and supply security."
        
        # Risk Consideration
        if winner.payment_terms_days == 0:
            risk = f"Advance payment requirement for {winner.vendor_name} may impact cash flow and working capital. Consider negotiating for at least 15-day credit terms. Monitor delivery performance closely as {winner.delivery_days}-day lead time requires careful schedule coordination."
        elif winner.payment_terms_days > 45:
            risk = f"Extended payment terms of {winner.payment_terms_days} days may indicate vendor cash flow concerns. Verify financial stability before large orders. {winner.delivery_days}-day delivery timeline should be monitored with milestone checkpoints."
        else:
            risk = f"{winner.vendor_name} shows {categories}. Standard payment terms of {winner.payment_terms_days} days align with industry practice. Monitor on-time delivery performance and quality consistency. Consider performance-based clauses in contract."
        
        # Project Impact
        if second:
            cost_diff = ((winner.price - second.price) / second.price * 100)
            if abs(cost_diff) > 5:
                impact = f"Choosing {winner.vendor_name} {'increases' if cost_diff > 0 else 'reduces'} total procurement cost by approximately {abs(cost_diff):.1f}% compared to {second.vendor_name}. The {winner.delivery_days}-day delivery timeline aligns with project schedule requirements. This decision prioritizes {priority} and maintains quality standards while managing budget constraints."
            else:
                impact = f"Choosing {winner.vendor_name} maintains cost neutrality (within 5% of alternatives) while offering {'better' if cost_diff < 0 else 'comparable'} payment terms. The {winner.delivery_days}-day delivery schedule supports project timeline. Decision optimizes for {priority} priority without significant budget impact."
        else:
            impact = f"Choosing {winner.vendor_name} as the sole supplier provides pricing certainty at ₹{winner.price:.0f}/unit with {winner.delivery_days}-day delivery. Project schedule accommodates lead time. Recommend establishing backup vendor relationships for supply chain resilience in future procurements."
        
        # Negotiation Tips
        tips = []
        if second:
            if winner.price > second.price:
                price_diff = winner.price - second.price
                tips.append(f"Leverage {second.vendor_name}'s lower price (₹{second.price:.0f}) to negotiate {price_diff:.0f} reduction per unit")
            if winner.payment_terms_days < second.payment_terms_days:
                tips.append(f"Request {second.payment_terms_days}-day credit terms matching {second.vendor_name}'s offer")
            if winner.delivery_days > second.delivery_days:
                tips.append(f"Negotiate for {second.delivery_days}-day delivery to match {second.vendor_name}'s timeline")
        
        tips.append("Inquire about volume discounts for orders exceeding current quantity by 20%+")
        tips.append("Request firm price validity for 90 days to allow for approval cycles")
        
        # Note about AI
        note = "\n\n*Note: AI-powered insights unavailable. Configure OPENROUTER_API_KEY in .env file for advanced recommendations with market intelligence and risk analysis.*"
        
        return AIInsights(
            primary_recommendation=primary_rec + note,
            alternate_strategy=alt_strategy,
            risk_consideration=risk,
            project_impact=impact,
            negotiation_tips=tips[:3]  # Top 3 tips
        )
