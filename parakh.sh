#!/usr/bin/env bash
# ===================================================================
#  परख (PARAKH) — भंडार की अपनी जाँच
#
#  चलाओ:  ./parakh.sh
#
#  यहाँ हर test असली process चलाता है: असली folder बनता है, असली
#  git repo बनता है, और असली script चलती है. कोई test सिर्फ़ string
#  मिलाकर पास नहीं होता — CLAUDE-CODE-COMMANDS.md का नियम ४ यही कहता है.
#
#  जो अभी नहीं जाँचा जा सकता, वो सबसे नीचे साफ़ लिखा है. उसे छिपाया
#  नहीं गया.
# ===================================================================

set -u

YAHAN="$(cd "$(dirname "$0")" && pwd)"
JAANCH="$YAHAN/aujaar/raaz_jaancho.py"

if [ -t 1 ]; then
    R=$'\033[0m'; B=$'\033[1m'; HARA=$'\033[32m'; LAL=$'\033[31m'
    DHUNDLA=$'\033[2m'
else
    R=""; B=""; HARA=""; LAL=""; DHUNDLA=""
fi

PASS=0; FAIL=0
AKHADA="$(mktemp -d)"
trap 'rm -rf "$AKHADA"' EXIT

# एक साफ़ git project बनाओ
project_banao() {
    local naam="$1"; local d="$AKHADA/$naam"
    mkdir -p "$d"
    git -C "$d" init -q .
    git -C "$d" config user.email "parakh@test"
    git -C "$d" config user.name  "Parakh"
    printf '.env\n*.pem\n__pycache__\nnode_modules\n' > "$d/.gitignore"
    printf 'print("namaste")\n' > "$d/app.py"
    echo "$d"
}

# जाँच चलाओ, exit code लौटाओ
jaancho_chalao() { python3 "$JAANCH" "$@" >/dev/null 2>&1; echo $?; }

kehna() {
    local naam="$1" chaha="$2" mila="$3"
    if [ "$chaha" = "$mila" ]; then
        printf "  ${HARA}[ पास ]${R}  %s\n" "$naam"
        PASS=$((PASS+1))
    else
        printf "  ${LAL}[ फेल ]${R}  %s  ${DHUNDLA}(चाहा=%s मिला=%s)${R}\n" \
               "$naam" "$chaha" "$mila"
        FAIL=$((FAIL+1))
    fi
}

echo
echo "${B}  परख — भंडार की अपनी जाँच${R}"
echo "  =============================================================="
echo "  अखाड़ा: $AKHADA"
echo

# ---------- राज़ जाँच ----------
echo "  ${B}राज़ जाँच${R}"

d="$(project_banao saaf)"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm pehla
kehna "साफ़ project पास होता है" 0 "$(jaancho_chalao "$d")"

d="$(project_banao khuli-key)"
printf 'KEY = "sk-abcdefghijklmnopqrstuvwxyz012345"\n' > "$d/conf.py"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm pehla
kehna "खुली पड़ी API key पकड़ी जाती है" 1 "$(jaancho_chalao "$d")"

# यही वो गड़बड़ थी जिससे सही project भी हमेशा रुक जाता था
d="$(project_banao gitignore-wali)"
printf 'KEY=sk-abcdefghijklmnopqrstuvwxyz012345\n' > "$d/.env"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm pehla
kehna ".gitignore की हुई .env पर नहीं रुकता" 0 "$(jaancho_chalao "$d")"

# और यही सबसे ख़तरनाक छेद था
d="$(project_banao itihaas-wali)"
printf 'TOKEN=ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n' > "$d/leak.txt"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm pehla
git -C "$d" rm -q leak.txt; git -C "$d" commit -qm "leak हटाई"
kehna "इतिहास में दबी key पकड़ी जाती है" 1 "$(jaancho_chalao "$d")"

d="$(project_banao maafi-wali)"
printf 'MISAAL = "sk-abcdefghijklmnopqrstuvwxyz012345"  # नक़ली\n' > "$d/misaal.py"
printf 'sk-abcdefghijklmnopqrstuvwxyz012345\n' > "$d/.raazignore"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm pehla
kehna ".raazignore से झूठा अलार्म माफ़ होता है" 0 "$(jaancho_chalao "$d")"

# नाम से पकड़ी गई file भी .raazignore से माफ़ होनी चाहिए — पर तभी जब
# उसमें सचमुच कोई राज़ न हो. दो हिस्से: पहले बिना माफ़ी रुकना चाहिए,
# फिर माफ़ी के साथ पास; और माफ़ी के बावजूद असली key नहीं छूटनी चाहिए.
d="$(project_banao naam-maafi)"
mkdir -p "$d/docker"
printf 'SECRET_KEY=CHANGEME\nPOSTGRES_PASSWORD=CHANGEME\n' > "$d/docker/.env.example"
printf '!.env.example\n' >> "$d/.gitignore"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm pehla
kehna "नाम से पकड़ी file बिना माफ़ी रोकती है" 1 "$(jaancho_chalao "$d")"

printf 'docker/.env.example\n' > "$d/.raazignore"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm doosra
kehna "माफ़ी के बाद वही file पास होती है" 0 "$(jaancho_chalao "$d")"

printf 'AWS_KEY=AKIAIOSFODNN7EXAMPLE\nsk-zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz\n' >> "$d/docker/.env.example"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm teesra
kehna "माफ़ी के बावजूद असली key नहीं छूटती" 1 "$(jaancho_chalao "$d")"

d="$AKHADA/bina-git"; mkdir -p "$d"
printf 'TOKEN=ghp_BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\n' > "$d/x.txt"
kehna "git नहीं है तो भी पूरा folder देखता है" 1 "$(jaancho_chalao "$d")"

d="$(project_banao sab-wala)"
printf 'KEY=sk-abcdefghijklmnopqrstuvwxyz012345\n' > "$d/.env"
git -C "$d" add -A >/dev/null; git -C "$d" commit -qm pehla
kehna "--sab से .gitignore वाली भी दिखती है" 1 "$(jaancho_chalao "$d" --sab)"

kehna "रास्ता ग़लत हो तो 2 लौटाता है" 2 "$(jaancho_chalao "$AKHADA/hai-hi-nahi")"
kehna "बिना रास्ते के 2 लौटाता है" 2 "$(python3 "$JAANCH" >/dev/null 2>&1; echo $?)"

# ---------- सूची पढ़ना ----------
echo
echo "  ${B}सूची पढ़ना${R}"

d="$(project_banao suchi-wala)"
NAKLI="$AKHADA/nakli"
mkdir -p "$NAKLI/aujaar"
cp "$YAHAN/bhandar.sh" "$NAKLI/"
cp "$JAANCH" "$NAKLI/aujaar/"

# Windows वाली file (CRLF) — पहले इससे आख़िरी खाने में \r चिपक जाता था
printf 'suchi-wala\t%s\tpublic\tब्योरा\r\n' "$d" > "$NAKLI/pariyojana.tsv"
out="$(cd "$NAKLI" && bash bhandar.sh dekho 2>&1)"
echo "$out" | grep -q 'suchi-wala' && mila=0 || mila=1
kehna "CRLF वाली सूची भी पढ़ी जाती है" 0 "$mila"
echo "$out" | grep -q 'git + remote\|git है, remote नहीं\|git नहीं है' \
    && mila=0 || mila=1
kehna "dekho project की हालत बताता है" 0 "$mila"

printf 'gayab\t%s/kahin-nahi\tpublic\tब्योरा\n' "$AKHADA" \
    > "$NAKLI/pariyojana.tsv"
out="$(cd "$NAKLI" && bash bhandar.sh dekho 2>&1)"
echo "$out" | grep -q 'folder नहीं मिला' && mila=0 || mila=1
kehna "ग़ायब folder पर टूटता नहीं, बताता है" 0 "$mila"

# ---------- हुक्म ----------
echo
echo "  ${B}हुक्म${R}"

out="$(cd "$NAKLI" && bash bhandar.sh koi-bhi-galat-hukum 2>&1)"
echo "$out" | grep -q 'dekho' && mila=0 || mila=1
kehna "ग़लत हुक्म पर मदद दिखाता है" 0 "$mila"

out="$(cd "$NAKLI" && bash bhandar.sh haal 2>&1)"
kehna "haal बिना गड़बड़ चलता है" 0 "$?"

# karo बिना पूछे कुछ न करे — terminal नहीं है, फिर भी सूची ख़ाली रखकर
# सिर्फ़ यह देखते हैं कि script सही ढंग से रुकती है (gh नहीं है तो).
bash -n "$YAHAN/bhandar.sh"
kehna "bhandar.sh का syntax ठीक है" 0 "$?"
python3 -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" \
    "$JAANCH" >/dev/null 2>&1
kehna "raaz_jaancho.py का syntax ठीक है" 0 "$?"

echo
echo "  =============================================================="
printf "  ${HARA}पास: %d${R}    ${LAL}फेल: %d${R}\n" "$PASS" "$FAIL"
echo
echo "  ${DHUNDLA}जो यहाँ नहीं जाँचा गया — और क्यों:${R}"
echo "  ${DHUNDLA}  'karo' का असली हिस्सा (gh repo create, git push) यहाँ${R}"
echo "  ${DHUNDLA}  नहीं चलता, क्योंकि उसके लिए GitHub पर सचमुच repo बनाना${R}"
echo "  ${DHUNDLA}  पड़ता. वो जाँच हाथ से करनी होगी — एक फ़ालतू private repo${R}"
echo "  ${DHUNDLA}  पर आज़माकर, फिर उसे हटाकर.${R}"
echo

[ "$FAIL" -eq 0 ]
