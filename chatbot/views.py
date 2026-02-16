import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services import query_chat


def _chat_json(reply, sources=None, status=200):
    """Response shape: reply, answer, sources (list of source names for citation)."""
    payload = {"reply": reply, "answer": reply}
    if sources is not None:
        payload["sources"] = sources
    return JsonResponse(payload, status=status)


@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    """
    Chat endpoint for Bedrock Knowledge Base RAG.
    Accepts JSON body with 'query', 'message', or 'question'.
    Returns JSON with 'reply', 'answer', and 'sources' (list of doc names).
    """
    try:
        body = json.loads(request.body) if request.body else {}
        question = (
            body.get("query") or body.get("message") or body.get("question") or ""
        ).strip()
        if not question:
            return _chat_json("Please enter a question.", sources=[], status=400)
        result = query_chat(question, request=request)
        return _chat_json(
            result["reply"],
            sources=result.get("sources", []),
            status=200,
        )
    except json.JSONDecodeError:
        return _chat_json("Invalid request.", sources=[], status=400)
