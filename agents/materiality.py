from typing import Dict, Any, List

def calculate_materiality(revenue: float = 0.0, profit_before_tax: float = 0.0, total_assets: float = 0.0) -> Dict[str, Any]:
    """
    Returns dict with recommended overall and performance materiality based on user-defined benchmarks.
    """
    benchmarks: List[Dict[str, Any]] = []
    
    if profit_before_tax > 0:
        overall = profit_before_tax * 0.05
        benchmarks.append({"benchmark": "Profit Before Tax", "rate": "5%", "overall": overall, "performance": overall * 0.75})
    
    if total_assets > 0:
        overall = total_assets * 0.02
        benchmarks.append({"benchmark": "Total Assets", "rate": "2%", "overall": overall, "performance": overall * 0.75})
        
    if revenue > 0:
        overall = revenue *  0.01
        benchmarks.append({"benchmark": "Total Revenue", "rate": "1%", "overall": overall, "performance": overall * 0.75})
        
    if benchmarks:
        return {"primary": benchmarks[0], "alternatives": benchmarks[1:]}  # type: ignore
    return {"error": "No valid benchmarks provided."}
