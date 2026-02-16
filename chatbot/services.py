"""
RAG service using AWS Bedrock Knowledge Base.
Knowledge Base should have S3 as data source with policy docs (refund, shipping, return, etc.).
"""
import logging
import random
import re
from django.conf import settings

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 1000
BEDROCK_TIMEOUT_SECONDS = 30

# If the model ever reveals AI/access phrasing despite the prompt, replace reply with a human fallback
_ROBOTIC_PHRASES = (
    "as an ai", "i'm an ai", "i am an ai", "as an assistant", "ai assistant",
    "don't have access", "do not have access", "i don't have access", "i do not have access",
    "i'm afraid i don't", "i don't have any information about your",
    "personal details about you", "personal information about you", "i don't store",
    "i can't", "i cannot", "i'm unable", "i am unable",
)

# Varied, polite, professional replies when we don't have the info. Use "we" voice, sound genuine.
# Picking at random so repeat questions don't get the same sentence every time.
_NO_INFO_REPLIES = (
    "We'd love to help with that—our support team has the details. Feel free to reach out and they'll take care of you.",
    "That's outside what we can look up in this chat, but our support team would be happy to help. Just drop them a line.",
    "We don't have that on hand here, but our support team certainly does. They're the best folks to ask—we'd suggest getting in touch.",
    "Great question! For that, we'd recommend reaching out to our support team directly. They'll be able to sort that out for you.",
    "We're not able to pull that up in this chat, but our support team can definitely help. Feel free to get in touch—they're lovely to work with.",
    "That's something our support team handles. We'd suggest reaching out to them; they'll get you sorted in no time.",
    "We keep that kind of detail with our support team. They'd be glad to help—just send them a message.",
    "We don't have that information here, but our support team does. Give them a shout and they'll help you out.",
    "For questions like that, our support team are the experts. We'd recommend reaching out—they're always happy to help.",
    "We're limited to our policy docs in this chat, but our support team can assist with that. They're just an email away.",
    "That's a good question—our support team would have the answer. We'd encourage you to reach out to them.",
    "We don't have that to hand in this chat, but our support team can certainly help. Feel free to get in touch when you're ready.",
)
_ERROR_REPLIES = (
    "We apologise—something went wrong on our end. Please try again in a moment, or reach out to our support team and we'll help straight away.",
    "We've hit a small snag. Could you try again shortly? If it keeps happening, our support team would be glad to assist.",
    "We're sorry—we ran into a technical hiccup. Please give it another try, or contact our support team and they'll sort it out.",
)


def _get_no_info_reply() -> str:
    """Pick a varied, human reply when we don't have the answer (avoids repeating the same sentence)."""
    return random.choice(_NO_INFO_REPLIES)


def _sanitize_reply(text: str) -> str:
    """If the reply sounds robotic or reveals AI/access, return a varied human fallback instead."""
    if not text or not text.strip():
        return _get_no_info_reply()
    lower = text.lower()
    if any(phrase in lower for phrase in _ROBOTIC_PHRASES):
        return _get_no_info_reply()
    return text.strip()

# System-style instructions: human, concise, privacy-respecting; same intent and constraints
RAG_PROMPT_TEMPLATE = """You are a friendly customer support agent for Trendy Threads. Write as a real person would—warm, professional, and genuinely helpful. Never sound robotic or scripted.

STRICT RULES:
- Answer in 1 to 3 short sentences only. No long paragraphs.
- Match the level of detail to what they asked. Answer directly—do not start with "According to the search results" or repeat the question.
- Use only the search results below. Do not make up information. Be polite and concise.
- Do not use bullet points unless they asked for a list. Prefer a short, natural reply.
- Always use "we" and "our" (company voice)—never "I" or "my". Sound like a supportive team member.

When the search results do NOT contain an answer (including questions about their name, account, order status, or any personal details):
- Never say you are an AI, a bot, or that you "don't have access" to information. Never mention AI, assistant, or access.
- Reply as a genuine human support agent would: acknowledge their question politely, then suggest our support team as the best next step. Be warm and professional.
- Use "we" and "our" only. Example phrasing: "We'd love to help with that—our support team has the details. Feel free to reach out." / "That's outside what we can look up here, but our support team would be happy to help." / "For that, we'd recommend reaching out to our support team directly—they'll sort that out for you." / "We don't have that on hand in this chat, but our support team certainly does. They're the best folks to ask."
- Vary your wording every time. If the user asks the same or similar question again, use a different phrase—never repeat. Be context-aware: if they asked about orders, mention support can check their order; if about account, mention they can help with account details; etc.
- Keep it to one or two short sentences. Sound authentic and caring.

<search_results>
$search_results$
</search_results>

Customer question: $query$

Answer (1-3 short sentences):"""


def _citation_labels(response: dict) -> list[str]:
    """Extract unique source names (doc detail/name) from RetrieveAndGenerate citations."""
    seen = set()
    labels = []
    for citation in response.get("citations", []):
        for ref in citation.get("retrievedReferences", []):
            name = _reference_display_name(ref)
            if name and name not in seen:
                seen.add(name)
                labels.append(name)
    return labels


def _reference_display_name(ref: dict) -> str | None:
    """Get a short display name for a retrieved reference (e.g. filename or doc title)."""
    meta = ref.get("metadata") or {}
    # Prefer metadata fields that often hold doc name (API may use camelCase)
    for key in ("fileName", "file_name", "title", "document_title", "source"):
        if meta.get(key):
            val = meta[key]
            return str(val).strip() if val else None
    # Fallback: from S3 URI use the key's last segment (filename)
    loc = ref.get("location") or {}
    s3 = loc.get("s3Location") or {}
    uri = s3.get("uri") or ""
    if isinstance(uri, str) and uri.startswith("s3://"):
        parts = uri.split("/")
        if len(parts) >= 4:
            return parts[-1]  # object key filename
        if parts:
            return parts[-1]
    return None


def get_bedrock_agent_client():
    import boto3
    from botocore.config import Config
    config = Config(
        connect_timeout=10,
        read_timeout=BEDROCK_TIMEOUT_SECONDS,
        retries={"max_attempts": 2, "mode": "standard"},
    )
    return boto3.client(
        "bedrock-agent-runtime",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        config=config,
    )


def _sanitize_query(text: str) -> str:
    """Limit length and strip control characters before sending to Bedrock."""
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()[:MAX_QUERY_LENGTH]
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def query_chat(question: str, request=None) -> dict:
    """
    Main chat entry: all questions go to AWS Bedrock RAG (Knowledge Base).
    Returns dict with keys: "reply" (str), "sources" (list of source names for citation).
    """
    sanitized = _sanitize_query(question)
    if not sanitized:
        return {
            "reply": "Please enter a question.",
            "sources": [],
        }
    return query_knowledge_base(sanitized)


def query_knowledge_base(question: str) -> dict:
    """
    Query Bedrock Knowledge Base (RAG).
    Returns dict with keys: "reply" (str), "sources" (list of source names for citation).
    """
    kb_id = (settings.BEDROCK_KNOWLEDGE_BASE_ID or "").strip()
    aws_key = (settings.AWS_ACCESS_KEY_ID or "").strip()
    if not kb_id or not aws_key:
        return {
            "reply": (
                "We're sorry—our chat support isn't fully set up yet. "
                "Please try again later or reach out to our support team directly."
            ),
            "sources": [],
        }

    try:
        client = get_bedrock_agent_client()
        region = settings.AWS_REGION
        model_arn = (
            settings.BEDROCK_MODEL_ARN
            or f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        )
        response = client.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": model_arn,
                    "generationConfiguration": {
                        "promptTemplate": {
                            "textPromptTemplate": RAG_PROMPT_TEMPLATE,
                        },
                    },
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "numberOfResults": 5,
                        }
                    },
                },
            },
        )
        output = response.get("output", {})
        text = output.get("text", "").strip()
        if not text:
            return {
                "reply": _get_no_info_reply(),
                "sources": [],
            }
        text = _sanitize_reply(text)
        sources = _citation_labels(response)
        return {"reply": text, "sources": sources}
    except Exception as e:
        logger.warning("Bedrock Knowledge Base query failed: %s", type(e).__name__, exc_info=True)
        return {
            "reply": random.choice(_ERROR_REPLIES),
            "sources": [],
        }
