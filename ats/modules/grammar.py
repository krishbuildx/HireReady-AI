"""Grammar checking with LanguageTool (falls back gracefully)."""
from __future__ import annotations

from typing import Dict, List


def check_grammar(text: str, max_matches: int = 25) -> Dict:
    try:
        import language_tool_python
        tool = language_tool_python.LanguageTool("en-US")
        matches = tool.check(text)
        issues: List[Dict] = []
        for m in matches[:max_matches]:
            issues.append({
                "message": m.message,
                "context": m.context,
                "suggestions": m.replacements[:3],
                "category": m.category,
            })
        total = len(matches)
        # Simple score: fewer issues = higher score
        words = max(len(text.split()), 1)
        density = total / words
        score = max(0, min(100, int(100 - density * 500)))
        try:
            tool.close()
        except Exception:
            pass
        return {"score": score, "total_issues": total, "issues": issues}
    except Exception as e:
        return {"score": 75, "total_issues": 0, "issues": [], "error": str(e)}
