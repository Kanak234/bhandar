#!/usr/bin/env bash
# ===================================================================
#  भंडार (BHANDAR) — सारे projects को GitHub पर चढ़ाने वाला script
#
#  चलाओ:
#      ./bhandar.sh dekho        सिर्फ़ दिखाओ, कुछ मत करो
#      ./bhandar.sh jaancho      हर project पर राज़-जाँच चलाओ
#      ./bhandar.sh karo         असल में repo बनाओ और push करो
#      ./bhandar.sh haal         कौन सा project कहाँ तक पहुँचा
#
#  ज़रूरी:
#      gh    — GitHub CLI       (sudo apt install gh)
#      git
#      python3
#
#  पहली बार:  gh auth login
# ===================================================================

set -u   # बिना बताए variable इस्तेमाल हो तो रुक जाओ
         # 'set -e' जान-बूझकर नहीं लगाया — एक project पर गड़बड़ हो तो
         # बाक़ी सब रुक जाते, और तब तुम्हें पता ही नहीं चलता कि कितने हुए.
         # हर project अपनी गलती ख़ुद सँभालता है, नीचे देखो.

YAHAN="$(cd "$(dirname "$0")" && pwd)"
SUCHI="$YAHAN/pariyojana.tsv"
BAHI="$YAHAN/bhandar-bahi.txt"

HUKUM="${1:-dekho}"

# ---------- रंग (terminal में) ----------
if [ -t 1 ]; then
    R=$'\033[0m'; B=$'\033[1m'; HARA=$'\033[32m'
    LAL=$'\033[31m'; PILA=$'\033[33m'; DHUNDLA=$'\033[2m'
else
    R=""; B=""; HARA=""; LAL=""; PILA=""; DHUNDLA=""
fi

kaho()  { printf "%s\n" "$*"; }
darj()  { printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$BAHI"; }

# ---------- ज़रूरी औज़ार हैं या नहीं ----------
aujaar_jaancho() {
    local kami=0
    for a in git python3; do
        if ! command -v "$a" >/dev/null 2>&1; then
            kaho "${LAL}  '$a' नहीं मिला.${R}"
            kami=1
        fi
    done
    if ! command -v gh >/dev/null 2>&1; then
        kaho "${LAL}  'gh' (GitHub CLI) नहीं मिला.${R}"
        kaho "     Ubuntu पर:  sudo apt install gh"
        kaho "     फिर:        gh auth login"
        kami=1
    elif ! gh auth status >/dev/null 2>&1; then
        kaho "${LAL}  gh तो है पर login नहीं है.${R}"
        kaho "     चलाओ:  gh auth login"
        kami=1
    fi
    return $kami
}

# ---------- सूची पढ़ो ----------
# हर लाइन:  नाम <TAB> रास्ता <TAB> public|private <TAB> ब्योरा
suchi_padho() {
    if [ ! -f "$SUCHI" ]; then
        kaho "${LAL}  pariyojana.tsv नहीं मिली.${R}"
        return 1
    fi
    grep -v '^#' "$SUCHI" | grep -v '^[[:space:]]*$'
}

# ---------- एक project पर राज़-जाँच ----------
raaz_jaancho() {
    local rasta="$1"
    python3 "$YAHAN/aujaar/raaz_jaancho.py" "$rasta" >/dev/null 2>&1
    return $?
}

# ---------- .gitignore बनाओ अगर नहीं है ----------
gitignore_banao() {
    local rasta="$1"
    local gi="$rasta/.gitignore"
    [ -f "$gi" ] && return 0
    cat > "$gi" << 'GIEOF'
# अपने आप बना — ज़रूरत के हिसाब से जोड़ते जाना

# गुप्त चीज़ें — ये कभी GitHub पर नहीं जानी चाहिए
.env
.env.*
*.pem
*.key
credentials.json
secrets.json
.netrc

# बनी हुई चीज़ें — ये दोबारा बन जाती हैं
__pycache__/
*.pyc
node_modules/
target/
dist/
build/
venv/
.venv/

# भारी चीज़ें — GitHub पर 100 MB की सीमा है
*.gguf
*.safetensors
*.pt
*.pth
*.onnx
*.bin

# मशीन की अपनी चीज़ें
.DS_Store
.vscode/
.idea/
GIEOF
    kaho "${DHUNDLA}       .gitignore बना दी${R}"
}

# ================= दिखाओ =================
hukum_dekho() {
    kaho ""
    kaho "${B}  भंडार — क्या-क्या होगा${R}"
    kaho "  =============================================================="
    kaho ""
    printf "  %-22s %-9s %s\n" "project" "कैसा" "हालत"
    kaho "  --------------------------------------------------------------"

    local kul=0 mile=0
    while IFS=$'\t' read -r naam rasta kaisa vivaran; do
        [ -z "${naam:-}" ] && continue
        kul=$((kul+1))
        rasta="${rasta/#\~/$HOME}"

        local hal
        if [ ! -d "$rasta" ]; then
            hal="${LAL}folder नहीं मिला${R}"
        else
            mile=$((mile+1))
            if [ -d "$rasta/.git" ]; then
                if git -C "$rasta" remote get-url origin >/dev/null 2>&1; then
                    hal="${HARA}git + remote${R}"
                else
                    hal="${PILA}git है, remote नहीं${R}"
                fi
            else
                hal="${PILA}git नहीं है${R}"
            fi
        fi
        printf "  %-22s %-9s %b\n" "$naam" "$kaisa" "$hal"
    done < <(suchi_padho)

    kaho "  --------------------------------------------------------------"
    kaho "  कुल $kul, मशीन पर मिले $mile"
    kaho ""
    kaho "  अब:  ./bhandar.sh jaancho    (push से पहले यह ज़रूरी है)"
    kaho ""
}

# ================= जाँचो =================
hukum_jaancho() {
    kaho ""
    kaho "${B}  राज़ जाँच — हर project पर${R}"
    kaho "  =============================================================="
    kaho ""

    local theek=0 gadbad=0
    while IFS=$'\t' read -r naam rasta kaisa vivaran; do
        [ -z "${naam:-}" ] && continue
        rasta="${rasta/#\~/$HOME}"
        [ ! -d "$rasta" ] && continue

        if raaz_jaancho "$rasta"; then
            printf "  ${HARA}[ साफ़ ]${R}  %-22s %s\n" "$naam" "$kaisa"
            theek=$((theek+1))
        else
            printf "  ${LAL}[ रुको ]${R}  %-22s %s\n" "$naam" "$kaisa"
            gadbad=$((gadbad+1))
        fi
    done < <(suchi_padho)

    kaho ""
    kaho "  साफ़: $theek    रुकने वाले: $gadbad"
    if [ "$gadbad" -gt 0 ]; then
        kaho ""
        kaho "${PILA}  जिन पर 'रुको' है, उन्हें अलग से देखो:${R}"
        kaho "      python3 aujaar/raaz_jaancho.py /रास्ता/project"
        kaho ""
        kaho "  सबसे सरल हल: उस project को private कर दो."
    fi
    kaho ""
}

# ================= करो =================
hukum_karo() {
    if ! aujaar_jaancho; then
        kaho ""
        kaho "${LAL}  पहले ऊपर वाली कमियाँ ठीक करो.${R}"
        kaho ""
        return 1
    fi

    local user
    user="$(gh api user --jq .login 2>/dev/null)"
    if [ -z "$user" ]; then
        kaho "${LAL}  GitHub username नहीं मिला. gh auth login चलाओ.${R}"
        return 1
    fi

    kaho ""
    kaho "${B}  भंडार — repo बना रहा हूँ  (खाता: $user)${R}"
    kaho "  =============================================================="
    darj "==== शुरू, खाता=$user ===="

    local hue=0 chhoote=0 pehle_se=0
    while IFS=$'\t' read -r naam rasta kaisa vivaran; do
        [ -z "${naam:-}" ] && continue
        rasta="${rasta/#\~/$HOME}"

        kaho ""
        kaho "  ${B}$naam${R}  ${DHUNDLA}($kaisa)${R}"

        # 1. folder है?
        if [ ! -d "$rasta" ]; then
            kaho "     ${PILA}छोड़ा — folder नहीं मिला: $rasta${R}"
            darj "$naam: छोड़ा, folder नहीं"
            chhoote=$((chhoote+1))
            continue
        fi

        # 2. public है तो राज़-जाँच पास करनी ही होगी
        #
        # यह शर्त सबसे ज़रूरी है. GitHub पर एक बार गई key वापस नहीं आती,
        # इसलिए यहाँ कोई ढील नहीं — जाँच फेल तो push नहीं.
        if [ "$kaisa" = "public" ]; then
            if ! raaz_jaancho "$rasta"; then
                kaho "     ${LAL}रुका — राज़ जाँच फेल. public नहीं करूँगा.${R}"
                kaho "     ${DHUNDLA}देखो: python3 aujaar/raaz_jaancho.py $rasta${R}"
                darj "$naam: रुका, राज़ जाँच फेल"
                chhoote=$((chhoote+1))
                continue
            fi
            kaho "     ${HARA}राज़ जाँच साफ़${R}"
        fi

        gitignore_banao "$rasta"

        # 3. git शुरू करो अगर नहीं है
        if [ ! -d "$rasta/.git" ]; then
            git -C "$rasta" init -q -b main 2>/dev/null || \
                { git -C "$rasta" init -q; git -C "$rasta" checkout -q -b main 2>/dev/null; }
            kaho "     git शुरू हुआ"
        fi

        # 4. commit करो अगर कुछ बाक़ी है
        git -C "$rasta" add -A 2>/dev/null
        if ! git -C "$rasta" diff --cached --quiet 2>/dev/null; then
            git -C "$rasta" -c user.name="Kanak Prabhakar" \
                commit -q -m "पहला commit — $vivaran" 2>/dev/null \
                && kaho "     commit हुआ" \
                || kaho "     ${PILA}commit नहीं हुआ (git की पहचान सेट है?)${R}"
        else
            kaho "     ${DHUNDLA}commit करने को कुछ नहीं${R}"
        fi

        # 5. repo बनाओ अगर नहीं है
        if gh repo view "$user/$naam" >/dev/null 2>&1; then
            kaho "     ${DHUNDLA}repo पहले से है${R}"
            pehle_se=$((pehle_se+1))
        else
            if gh repo create "$naam" "--$kaisa" \
                    --description "$vivaran" >/dev/null 2>&1; then
                kaho "     ${HARA}repo बना — $kaisa${R}"
                darj "$naam: repo बना ($kaisa)"
            else
                kaho "     ${LAL}repo नहीं बना${R}"
                darj "$naam: repo बनाने में गड़बड़"
                chhoote=$((chhoote+1))
                continue
            fi
        fi

        # 6. remote जोड़ो
        if ! git -C "$rasta" remote get-url origin >/dev/null 2>&1; then
            git -C "$rasta" remote add origin \
                "https://github.com/$user/$naam.git"
            kaho "     remote जुड़ा"
        fi

        # 7. push
        if git -C "$rasta" push -q -u origin main 2>/dev/null || \
           git -C "$rasta" push -q -u origin master 2>/dev/null; then
            kaho "     ${HARA}push हुआ  ->  github.com/$user/$naam${R}"
            darj "$naam: push हुआ"
            hue=$((hue+1))
        else
            kaho "     ${LAL}push नहीं हुआ${R}"
            kaho "     ${DHUNDLA}हाथ से देखो: cd $rasta && git push -u origin main${R}"
            darj "$naam: push में गड़बड़"
            chhoote=$((chhoote+1))
        fi

    done < <(suchi_padho)

    kaho ""
    kaho "  =============================================================="
    kaho "  ${HARA}हुए: $hue${R}    ${PILA}पहले से थे: $pehle_se${R}    ${LAL}छूटे: $chhoote${R}"
    kaho "  बही: $BAHI"
    kaho ""
    darj "==== ख़त्म: हुए=$hue पहले_से=$pehle_se छूटे=$chhoote ===="
}

# ================= हाल =================
hukum_haal() {
    kaho ""
    kaho "${B}  हाल${R}"
    kaho "  =============================================================="
    kaho ""
    while IFS=$'\t' read -r naam rasta kaisa vivaran; do
        [ -z "${naam:-}" ] && continue
        rasta="${rasta/#\~/$HOME}"
        [ ! -d "$rasta/.git" ] && continue

        local bina_commit
        bina_commit="$(git -C "$rasta" status --porcelain 2>/dev/null | wc -l)"
        local aage
        aage="$(git -C "$rasta" rev-list --count @{u}..HEAD 2>/dev/null || echo "?")"

        printf "  %-22s " "$naam"
        if [ "$bina_commit" -gt 0 ]; then
            printf "${PILA}%s files बिना commit${R}  " "$bina_commit"
        fi
        if [ "$aage" != "0" ] && [ "$aage" != "?" ]; then
            printf "${PILA}%s commit बिना push${R}" "$aage"
        fi
        if [ "$bina_commit" -eq 0 ] && [ "$aage" = "0" ]; then
            printf "${HARA}सब चढ़ा हुआ है${R}"
        fi
        printf "\n"
    done < <(suchi_padho)
    kaho ""
}

# ================= मुख्य =================
case "$HUKUM" in
    dekho)   hukum_dekho ;;
    jaancho) hukum_jaancho ;;
    karo)    hukum_karo ;;
    haal)    hukum_haal ;;
    *)
        kaho ""
        kaho "  ./bhandar.sh dekho      क्या-क्या होगा, कुछ बदले बिना"
        kaho "  ./bhandar.sh jaancho    राज़ जाँच — push से पहले ज़रूरी"
        kaho "  ./bhandar.sh karo       repo बनाओ और push करो"
        kaho "  ./bhandar.sh haal       कौन कहाँ तक पहुँचा"
        kaho ""
        ;;
esac
