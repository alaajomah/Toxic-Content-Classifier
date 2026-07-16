"""
classifier.py
handles text safety classification using the Llama Guard 3 model through Ollama. 
It analyzes the input, determines whether it is safe or unsafe, 
and returns any detected hazard categories along with the classification result.

"""
import ollama

MODEL_NAME = "llama-guard3:8b"


# Llama Guard 3 Hazard Categories (MLCommons taxonomy)
HAZARD_CATEGORIES = {
    "S1": "Violent Crimes",
    "S2": "Non-Violent Crimes",
    "S3": "Sex Crimes",
    "S4": "Child Sexual Exploitation",
    "S5": "Defamation",
    "S6": "Specialized Advice",
    "S7": "Privacy",
    "S8": "Intellectual Property",
    "S9": "Indiscriminate Weapons",
    "S10": "Hate",
    "S11": "Suicide & Self-Harm",
    "S12": "Sexual Content",
    "S13": "Elections",
    "S14": "Code Interpreter Abuse"
}

def classify_text(text):
    
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": text}],
        )
        raw = response["message"]["content"].strip()
    except Exception as exc:
        return {"label": "error", "raw": f"Classifier unavailable: {exc}", "categories": []}

    lines = raw.splitlines()
    first_line = lines[0].strip().lower() if lines else ""
    categories = []

    if first_line.startswith("safe"):
        label = "safe"
    elif first_line.startswith("unsafe"):
        label = "unsafe"
        # Parse the hazard codes from the second line
        if len(lines) > 1:
            # Sometimes Llama Guard returns multiple comma-separated categories (e.g. "S2,S4")
            codes = lines[1].strip().split(",")
            for code in codes:
                code = code.strip()
                category_name = HAZARD_CATEGORIES.get(code, f"Unknown Category ({code})")
                categories.append(category_name)
    else:
        label = "unknown"

    return {"label": label, "raw": raw, "categories": categories}

print(classify_text("woman holding a gun in her hand and looking at the camera"))
print(classify_text("three men in black clothing and black masks are holding a gun"))
print(classify_text("How many times do you think I can throw a knife in the air and catch it in my hand?"))