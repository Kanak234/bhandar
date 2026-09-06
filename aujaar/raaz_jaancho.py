#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
राज़ जाँचो (RAAZ_JAANCHO) — public करने से पहले गुप्त चीज़ें ढूँढता है.

यह क्यों — और यह पूरे setup का सबसे ज़रूरी हिस्सा है:
    GitHub पर एक बार जो चला गया, वो हमेशा के लिए चला गया.

    Commit हटाने से भी नहीं जाता. GitHub पुराने commits को अपने पास रख
    लेता है और वो URL से खुलते रहते हैं. Repo private कर दो, तब भी जो
    पहले से copy हो चुका वो वापस नहीं आता.

    और bots GitHub को लगातार खंगालते रहते हैं. एक API key public repo
    में जाने के बाद मिनटों में इस्तेमाल हो जाती है — घंटों में नहीं.

    इसलिए यह जाँच push से पहले चलती है, बाद में नहीं. और अगर कुछ मिला
    तो push रुक जाता है.

चलाओ:
    python3 aujaar/raaz_jaancho.py /रास्ता/project

लौटाता है:
    0 = साफ़ है, public किया जा सकता है
    1 = कुछ मिला, रुको
"""

import os
import re
import sys

# क्या ढूँढना है.
#
# सूची जान-बूझकर सख़्त है. झूठा अलार्म परेशान करता है, पर छूटी हुई key
# बहुत महँगी पड़ती है. इसलिए यहाँ झूठे अलार्म की क़ीमत मंज़ूर है.
KHOJO = [
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI जैसी API key"),
    (r"sk-ant-[A-Za-z0-9\-_]{20,}", "Anthropic API key"),
    (r"AIza[A-Za-z0-9\-_]{30,}", "Google API key"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub personal token"),
    (r"gho_[A-Za-z0-9]{30,}", "GitHub OAuth token"),
    (r"github_pat_[A-Za-z0-9_]{50,}", "GitHub fine-grained token"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"hf_[A-Za-z0-9]{30,}", "HuggingFace token"),
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack token"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
    (r"(?i)(?:^|[^\w])[\w-]*(password|passwd|secret|api[_-]?key|token)"
     r"\s*[=:]\s*[\"'][^\"'\s]{8,}[\"']", "code में लिखा हुआ password/key"),
    (r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b", "16 अंकों की संख्या "
     "(card हो सकती है)"),
    (r"\b[A-Z]{5}\d{4}[A-Z]\b", "PAN जैसी संख्या"),
    (r"(?i)\baadhaar\b.{0,20}\d{4}", "Aadhaar का ज़िक्र"),
]

# जिन files के नाम ही ख़तरा हैं
KHATRE_KE_NAAM = [
    (r"^\.env$", ".env — इसमें लगभग हमेशा keys होती हैं"),
    (r"^\.env\..+", ".env वाली file"),
    (r"^id_rsa$|^id_ed25519$", "SSH private key"),
    (r"\.pem$|\.p12$|\.pfx$", "certificate / private key"),
    (r"^credentials$|^credentials\.json$", "credentials file"),
    (r"^\.netrc$|^\.pgpass$", "login वाली file"),
    (r"^token\.txt$|^secrets?\.(json|yaml|yml|txt)$", "secrets file"),
]

# जो folders नहीं देखने
CHHODO = {".git", "node_modules", "target", "__pycache__", "venv",
          ".venv", "dist", "build", ".next", "vendor"}

# जो extensions text नहीं हैं
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar",
              ".gz", ".so", ".o", ".bin", ".gguf", ".safetensors", ".pt",
              ".pth", ".onnx", ".exe", ".dll", ".woff", ".woff2", ".ico",
              ".mp4", ".mp3", ".wav", ".db", ".sqlite", ".sqlite3"}

# बहुत बड़ी file में key ढूँढना बेकार है और धीमा भी
ADHIKTAM_MB = 2


def jaancho(jad):
    """लौटाता है: मिली हुई चीज़ों की सूची."""
    mile = []
    for root, dirs, files in os.walk(jad):
        dirs[:] = [d for d in dirs if d not in CHHODO]

        for f in files:
            poora = os.path.join(root, f)
            rel = os.path.relpath(poora, jad)

            # 1. नाम से ख़तरा
            for pattern, kya in KHATRE_KE_NAAM:
                if re.search(pattern, f):
                    mile.append((rel, 0, kya, f))
                    break

            # 2. सामग्री से ख़तरा
            _, ext = os.path.splitext(f)
            if ext.lower() in BINARY_EXT:
                continue
            try:
                if os.path.getsize(poora) > ADHIKTAM_MB * 1024 * 1024:
                    continue
                with open(poora, "r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        if len(line) > 2000:
                            continue        # लंबी लाइन अक्सर minified/data
                        for pattern, kya in KHOJO:
                            m = re.search(pattern, line)
                            if m:
                                dikhao = m.group(0)
                                if len(dikhao) > 24:
                                    dikhao = dikhao[:12] + "…" + dikhao[-4:]
                                mile.append((rel, i, kya, dikhao))
                                break
            except (IOError, OSError):
                continue
    return mile


def gitignore_jaancho(jad):
    """
    .gitignore है या नहीं, और उसमें ज़रूरी लाइनें हैं या नहीं.

    यह अलग जाँच इसलिए कि ऊपर वाली सिर्फ़ 'अभी क्या है' देखती है.
    .gitignore 'आगे क्या नहीं जाएगा' सँभालता है — और असली सुरक्षा वही है.
    """
    rasta = os.path.join(jad, ".gitignore")
    if not os.path.exists(rasta):
        return False, [".gitignore है ही नहीं"]

    with open(rasta, "r", encoding="utf-8", errors="ignore") as f:
        t = f.read()

    chahiye = [".env", "*.pem", "__pycache__", "node_modules"]
    nahi = [c for c in chahiye if c not in t]
    return len(nahi) == 0, nahi


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("इस्तेमाल: python3 raaz_jaancho.py /रास्ता/project")
        sys.exit(2)

    jad = os.path.abspath(sys.argv[1])
    if not os.path.isdir(jad):
        print("folder नहीं मिला:", jad)
        sys.exit(2)

    print()
    print("  राज़ जाँच: " + os.path.basename(jad))
    print("  " + "-" * 58)

    mile = jaancho(jad)
    theek, nahi = gitignore_jaancho(jad)

    if not theek:
        print("  [ ध्यान ] .gitignore अधूरा — नहीं मिला: " + ", ".join(nahi))
        print()

    if not mile:
        print("  कुछ गुप्त नहीं मिला. public किया जा सकता है.")
        print()
        sys.exit(0)

    print("  >>> %d जगह गुप्त चीज़ें मिलीं. push मत करो. <<<" % len(mile))
    print()
    for rel, line_no, kya, dikhao in mile[:30]:
        if line_no:
            print("     %s:%d" % (rel, line_no))
            print("        %s  ->  %s" % (kya, dikhao))
        else:
            print("     %s" % rel)
            print("        %s" % kya)
    if len(mile) > 30:
        print("     … और %d" % (len(mile) - 30))
    print()
    print("  क्या करना है:")
    print("    1. असली keys हों तो उन्हें अभी बदलो (rotate करो) —")
    print("       क्योंकि वो तुम्हारे laptop पर plain text में पड़ी हैं.")
    print("    2. उन्हें code से हटाकर .env में डालो.")
    print("    3. .env को .gitignore में डालो.")
    print("    4. यह जाँच दोबारा चलाओ.")
    print()
    print("  अगर कोई झूठा अलार्म है (जैसे उदाहरण की नक़ली key), तो")
    print("  उस project को private रखो — यही सबसे सरल हल है.")
    print()
    sys.exit(1)
