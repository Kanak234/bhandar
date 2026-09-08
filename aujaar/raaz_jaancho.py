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

यह जाँच किस चीज़ को देखती है — यह समझना ज़रूरी है:
    push वो चीज़ भेजता है जो git के पास है, वो नहीं जो folder में पड़ी है.
    ये दोनों एक नहीं हैं. इसलिए जाँच दो हिस्सों में है:

      १. अभी की files  — पर सिर्फ़ वो जो git सचमुच भेजेगा.
                          .gitignore की हुई file कभी नहीं जाती, इसलिए
                          उस पर रोक लगाना बेमानी है.

      २. पुराना इतिहास — जो commit हो चुका वो push में जाता है, चाहे
                          file अब folder से हट चुकी हो. पहले यह जाँच
                          नहीं थी, और यही सबसे ख़तरनाक छेद था.

चलाओ:
    python3 aujaar/raaz_jaancho.py /रास्ता/project
    python3 aujaar/raaz_jaancho.py /रास्ता/project --sab   (गैर-git files भी)

लौटाता है:
    0 = साफ़ है, public किया जा सकता है
    1 = कुछ मिला, रुको
    2 = इस्तेमाल में गड़बड़ (रास्ता नहीं मिला वग़ैरह)
"""

import os
import re
import subprocess
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

# इतिहास कितना पढ़ें. बहुत पुराने बड़े repo में पूरा इतिहास पढ़ना धीमा है,
# इसलिए एक हद रखी है — और हद लगे तो साफ़ बता देते हैं, चुपचाप नहीं छोड़ते.
ITIHAAS_ADHIKTAM_MB = 40

# जिन झूठे अलार्म को माफ़ करना है, वो इस file में लिखे जाते हैं.
# हर लाइन एक टुकड़ा — जिस लाइन में वो टुकड़ा मिला, वो छोड़ दी जाती है.
MAAFI_FILE = ".raazignore"


def _chalao(jad, *args):
    """git चलाओ. लौटाता है (theek, output)."""
    try:
        n = subprocess.run(["git", "-C", jad] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=120)
        return n.returncode == 0, n.stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        return False, ""


def git_hai(jad):
    theek, out = _chalao(jad, "rev-parse", "--is-inside-work-tree")
    return theek and out.strip() == "true"


def maafi_padho(jad):
    """.raazignore से माफ़ किए हुए टुकड़े पढ़ो."""
    rasta = os.path.join(jad, MAAFI_FILE)
    if not os.path.exists(rasta):
        return []
    tukde = []
    with open(rasta, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                tukde.append(line)
    return tukde


def maaf_hai(line, tukde):
    return any(t in line for t in tukde)


def _line_jaancho(line, tukde):
    """एक लाइन में गुप्त चीज़ ढूँढो. लौटाता है (kya, dikhao) या None."""
    if len(line) > 2000:
        return None          # लंबी लाइन अक्सर minified/data
    if maaf_hai(line, tukde):
        return None
    for pattern, kya in KHOJO:
        m = re.search(pattern, line)
        if m:
            dikhao = m.group(0)
            if len(dikhao) > 24:
                dikhao = dikhao[:12] + "…" + dikhao[-4:]
            return kya, dikhao
    return None


def bhejne_wali_files(jad):
    """
    git सचमुच किन files को भेजेगा.

    यही असली सवाल है. पहले यह जाँच हर file देखती थी, इसलिए ठीक से
    .gitignore की हुई .env पर भी रुक जाती थी — और वो file कभी push
    होती ही नहीं. उससे जाँच बेकार हो जाती थी: सही काम करने वाला
    project भी हमेशा 'रुको' दिखाता था.

    लौटाता है (files की सूची, git_hai).
    """
    if not git_hai(jad):
        return None, False

    # tracked + वो untracked जो ignore नहीं हैं — यही push में जाएँगे
    theek, out = _chalao(jad, "ls-files", "--cached", "--others",
                         "--exclude-standard", "-z")
    if not theek:
        return None, True
    return [f for f in out.split("\0") if f], True


def sab_files(jad):
    """git नहीं है तो पूरा folder देखो (पुराना तरीक़ा)."""
    mile = []
    for root, dirs, files in os.walk(jad):
        dirs[:] = [d for d in dirs if d not in CHHODO]
        for f in files:
            mile.append(os.path.relpath(os.path.join(root, f), jad))
    return mile


def files_jaancho(jad, files, tukde):
    """दी हुई files में गुप्त चीज़ें ढूँढो."""
    mile = []
    for rel in files:
        poora = os.path.join(jad, rel)
        naam = os.path.basename(rel)

        # 1. नाम से ख़तरा
        for pattern, kya in KHATRE_KE_NAAM:
            if re.search(pattern, naam):
                mile.append((rel, 0, kya, naam))
                break

        # 2. सामग्री से ख़तरा
        _, ext = os.path.splitext(naam)
        if ext.lower() in BINARY_EXT:
            continue
        try:
            if os.path.getsize(poora) > ADHIKTAM_MB * 1024 * 1024:
                continue
            with open(poora, "r", encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    got = _line_jaancho(line, tukde)
                    if got:
                        mile.append((rel, i, got[0], got[1]))
                        break
        except (IOError, OSError):
            continue
    return mile


def itihaas_jaancho(jad, tukde):
    """
    पुराने commits में गुप्त चीज़ें ढूँढो.

    यह सबसे ज़रूरी जाँच है और पहले यह थी ही नहीं.

    वजह: `git push` वो सब भेजता है जो commit हो चुका है. अगर key एक
    बार commit हुई और अगले commit में file हटा दी गई, तो folder साफ़
    दिखता है — पर key इतिहास में बैठी है और push के साथ GitHub पर
    चली जाती है. पुरानी जाँच ऐसे project को "साफ़ है" कह देती थी.

    लौटाता है (मिली हुई चीज़ें, hadd_lagi).
    """
    if not git_hai(jad):
        return [], False

    theek, _ = _chalao(jad, "rev-parse", "--verify", "HEAD")
    if not theek:
        return [], False     # अभी कोई commit ही नहीं

    try:
        n = subprocess.Popen(
            ["git", "-C", jad, "log", "--all", "--no-color", "-p", "-U0",
             "--format=commit %h %s"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return [], False

    mile = []
    dekha = set()
    commit = "?"
    file_ab = "?"
    padha = 0
    hadd = ITIHAAS_ADHIKTAM_MB * 1024 * 1024
    hadd_lagi = False

    try:
        for raw in n.stdout:
            padha += len(raw)
            if padha > hadd:
                hadd_lagi = True
                break
            line = raw.decode("utf-8", "replace").rstrip("\n")

            if line.startswith("commit "):
                commit = line[7:]
                continue
            if line.startswith("+++ b/"):
                file_ab = line[6:]
                continue
            if not line.startswith("+") or line.startswith("+++"):
                continue

            got = _line_jaancho(line[1:], tukde)
            if got:
                # एक ही key कई commits में दिखती है — एक बार ही बताओ
                chaabi = (file_ab, got[1])
                if chaabi in dekha:
                    continue
                dekha.add(chaabi)
                mile.append((file_ab, commit, got[0], got[1]))
    finally:
        try:
            n.stdout.close()
            n.kill()
            n.wait(timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass

    return mile, hadd_lagi


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


def main(argv):
    if len(argv) < 2:
        print("इस्तेमाल: python3 raaz_jaancho.py /रास्ता/project [--sab]")
        return 2

    sab = "--sab" in argv[1:]
    rasta_args = [a for a in argv[1:] if not a.startswith("--")]
    if not rasta_args:
        print("इस्तेमाल: python3 raaz_jaancho.py /रास्ता/project [--sab]")
        return 2

    jad = os.path.abspath(rasta_args[0])
    if not os.path.isdir(jad):
        print("folder नहीं मिला:", jad)
        return 2

    tukde = maafi_padho(jad)

    print()
    print("  राज़ जाँच: " + os.path.basename(jad))
    print("  " + "-" * 58)

    files, is_git = bhejne_wali_files(jad)
    if files is None or sab:
        files = sab_files(jad)
        dayra = "पूरा folder"
    else:
        dayra = "वो files जो git भेजेगा (%d)" % len(files)

    ab_mile = files_jaancho(jad, files, tukde)
    itihaas_mile, hadd_lagi = itihaas_jaancho(jad, tukde)
    theek, nahi = gitignore_jaancho(jad)

    print("  देखा: " + dayra)
    if is_git:
        print("  इतिहास: " + ("देखा" if not hadd_lagi else
                              "देखा (पर %d MB की हद लग गई — पूरा नहीं)"
                              % ITIHAAS_ADHIKTAM_MB))
    else:
        print("  इतिहास: git नहीं है, इसलिए कुछ नहीं")
    print()

    if not theek:
        print("  [ ध्यान ] .gitignore अधूरा — नहीं मिला: " + ", ".join(nahi))
        print()

    kul = len(ab_mile) + len(itihaas_mile)
    if kul == 0:
        if hadd_lagi:
            print("  कुछ गुप्त नहीं मिला — पर इतिहास पूरा नहीं देखा जा सका.")
            print("  बड़े repo में हाथ से देख लेना बेहतर है.")
        else:
            print("  कुछ गुप्त नहीं मिला. public किया जा सकता है.")
        print()
        return 0

    print("  >>> %d जगह गुप्त चीज़ें मिलीं. push मत करो. <<<" % kul)
    print()

    if ab_mile:
        print("  — अभी की files में —")
        for rel, line_no, kya, dikhao in ab_mile[:30]:
            if line_no:
                print("     %s:%d" % (rel, line_no))
                print("        %s  ->  %s" % (kya, dikhao))
            else:
                print("     %s" % rel)
                print("        %s" % kya)
        if len(ab_mile) > 30:
            print("     … और %d" % (len(ab_mile) - 30))
        print()

    if itihaas_mile:
        print("  — पुराने commits में (file अब भले न हो) —")
        for rel, commit, kya, dikhao in itihaas_mile[:30]:
            print("     %s   (commit %s)" % (rel, commit))
            print("        %s  ->  %s" % (kya, dikhao))
        if len(itihaas_mile) > 30:
            print("     … और %d" % (len(itihaas_mile) - 30))
        print()
        print("  ध्यान से पढ़ो: यह इतिहास में है. file हटाने से यह नहीं")
        print("  जाती — push करते ही GitHub पर चली जाएगी.")
        print()

    print("  क्या करना है:")
    print("    1. असली keys हों तो उन्हें अभी बदलो (rotate करो) —")
    print("       क्योंकि वो तुम्हारे laptop पर plain text में पड़ी हैं.")
    print("    2. उन्हें code से हटाकर .env में डालो.")
    print("    3. .env को .gitignore में डालो.")
    if itihaas_mile:
        print("    4. इतिहास वाली के लिए इतना काफ़ी नहीं. या तो उस project")
        print("       को private रखो, या इतिहास नए सिरे से बनाओ:")
        print("           rm -rf .git && git init")
        print("       (पुराने commits चले जाएँगे — सोचकर करना.)")
        print("    5. यह जाँच दोबारा चलाओ.")
    else:
        print("    4. यह जाँच दोबारा चलाओ.")
    print()
    print("  अगर कोई झूठा अलार्म है (जैसे उदाहरण की नक़ली key), तो उस")
    print("  लाइन का टुकड़ा %s में लिख दो, या project private रखो." % MAAFI_FILE)
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
