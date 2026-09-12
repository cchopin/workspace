def input_guardrail(prompt):
    import re
    if "packetsnacc.local" in prompt:
        raise GuardrailException("Invalid URL")
    prompt = re.sub(r"[^A-Za-z0-9\s.:/_@-]", "", prompt)
    prompt = prompt[:512]
    return prompt

def output_guardrail(response):
    import json, re, html, validators
    try:
        obj = json.loads(response)
    except Exception:
        raise GuardrailException("Invalid JSON")
    if not isinstance(obj, dict) or "type" not in obj or "response" not in obj:
        raise GuardrailException("Invalid JSON")
    t = obj["type"]
    if t not in ("text", "url"):
        raise GuardrailException("Invalid JSON")
    if t == "url":
        val = obj["response"]
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", val)
        scheme = m.group(1).lower() if m else None
        if scheme and scheme not in ("http", "https"):
            raise GuardrailException("Invalid URL scheme")
        if not validators.url(val):
            raise GuardrailException("Invalid URL")
        return json.dumps(obj)
    else:
        obj["response"] = html.escape(obj["response"])
        return json.dumps(obj)
