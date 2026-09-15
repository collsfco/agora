import json
import asyncio
from pathlib import Path
from app.agents.router import pre_route_user_message, detect_response_language
from app.policy.tool_policy import get_allowed_tools_for_domain

CASES_FILE = Path(__file__).resolve().parent / "cases" / "test_cases.json"

def run_evals():
    print("=" * 60)
    print("🧪 EJECUTANDO SUITE DE EVALUACIÓN DE AGENTES (AGORA EVALS)")
    print("=" * 60)
    
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    passed = 0
    total = len(cases)
    
    for case in cases:
        cid = case["id"]
        query = case["query"]
        expected_domain = case["expected_domain"]
        expected_lang = case["expected_lang"]
        expected_tool = case["expected_tool"]
        
        # 1. Test Router & Language
        domain, requires_fresh = pre_route_user_message(query)
        lang = detect_response_language(query)
        allowed_tools = get_allowed_tools_for_domain(domain, "principal_a")
        
        domain_ok = (domain == expected_domain)
        lang_ok = (lang == expected_lang)
        tool_ok = True
        if expected_tool:
            tool_ok = expected_tool in allowed_tools
        elif expected_domain == "general":
            tool_ok = len(allowed_tools) == 0
            
        case_passed = domain_ok and lang_ok and tool_ok
        status = "✅ PASS" if case_passed else "❌ FAIL"
        if case_passed:
            passed += 1
            
        print(f"[{status}] {cid}: '{query[:45]}...'")
        print(f"       Domain: {domain} (Exp: {expected_domain}) | Lang: {lang} (Exp: {expected_lang}) | Tools: {len(allowed_tools)}")
        if not case_passed:
            print(f"       ↳ Fallo detectado en validación.")
            
    print("=" * 60)
    score_pct = (passed / total) * 100
    print(f"📊 RESULTADO FINAL: {passed}/{total} tests superados ({score_pct:.1f}%)")
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    run_evals()
