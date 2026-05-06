import re
from app.core.gemma_engine import chat, reset
from app.core.function_caller import run_agent
from app.core.triage_logic import assess_severity
from app.core.voice_handler import speak, listen
from app.core.image_analyzer import analyze_image
from app.utils.local_db import init_db, log_visit, get_stats

BANNER = """
╔══════════════════════════════════════════════════════╗
║                    MEDI v1.0                         ║
║     Offline AI Copilot for Frontline Health Workers  ║
║          Powered by Gemma 4 — No Internet Needed     ║
╚══════════════════════════════════════════════════════╝
"""

LANGUAGES = {
    "1":  ("English",    "en",       "Hello! I am Medi. Tell me about your patient."),
    "2":  ("Roman Urdu", "ur-roman", "Assalam! Main Medi hun. Apne mareez ke baare mein batayen."),
    "3":  ("اردو",       "ur",       "السلام علیکم! میں میڈی ہوں۔ اپنے مریض کے بارے میں بتائیں۔"),
    "4":  ("हिंदी",      "hi",       "नमस्ते! मैं Medi हूँ। अपने मरीज़ के बारे में बताएं।"),
    "5":  ("Hausa",      "ha",       "Sannu! Ni ne Medi. Gaya min game da majiyyacinka."),
    "6":  ("Swahili",    "sw",       "Habari! Mimi ni Medi. Niambie kuhusu mgonjwa wako."),
    "7":  ("Français",   "fr",       "Bonjour! Je suis Medi. Parlez-moi de votre patient."),
    "8":  ("বাংলা",      "bn",       "হ্যালো! আমি Medi। আপনার রোগী সম্পর্কে বলুন।"),
    "9":  ("Tagalog",    "tl",       "Kamusta! Ako si Medi. Sabihin sa akin ang tungkol sa iyong pasyente."),
    "10": ("አማርኛ",       "am",       "ሰላም! እኔ Medi ነኝ። ስለ ታካሚዎ ይንገሩኝ።"),
    "11": ("پښتو",       "ps",       "سلام! زه Medi یم. د خپل ناروغ په اړه راته ووایاست."),
    "12": ("Soomaali",   "so",       "Salaam! Aniga waxaan ahay Medi. Igu warran bukaankaaga."),
    "13": ("Português",  "pt",       "Olá! Eu sou Medi. Fale-me sobre seu paciente."),
    "14": ("Español",    "es",       "¡Hola! Soy Medi. Háblame de tu paciente."),
    "15": ("Indonesian", "id",       "Halo! Saya Medi. Ceritakan tentang pasien Anda."),
    "16": ("Yoruba",     "yo",       "Ẹ káàbọ̀! Èmi ni Medi. Sọ fún mi nípa ọmọ aláìsàn rẹ."),
    "17": ("Igbo",       "ig",       "Nnọọ! Abụ m Medi. Gwa m maka ọrịa gị."),
    "18": ("Zulu",       "zu",       "Sawubona! Ngi-Medi. Ngixoxele ngegula lakho."),
    "19": ("Tigrinya",   "ti",       "ሰላም! ኣነ Medi እየ። ብዛዕባ ሕሙምካ ንገረኒ።"),
    "20": ("Burmese",    "my",       "မင်္ဂလာပါ! ကျွန်တော် Medi ပါ။ လူနာအကြောင်း ပြောပြပါ။"),
    "21": ("Khmer",      "km",       "សួស្តី! ខ្ញុំជា Medi។ សូមប្រាប់ខ្ញុំអំពីអ្នកជំងឺ។"),
    "22": ("Nepali",     "ne",       "नमस्ते! म Medi हुँ। आफ्नो बिरामीको बारेमा बताउनुस्।"),
}

LANG_DESCRIPTIONS = {
    "en":       "Clinical guidance — Global / English",
    "ur-roman": "Roman Urdu mein madad — Pakistan/India",
    "ur":       "اردو میں طبی رہنمائی — پاکستان",
    "hi":       "हिंदी में मार्गदर्शन — भारत",
    "ha":       "Taimako na likitanci — Najeriya/Nijar/Ghana",
    "sw":       "Mwongozo wa afya — Afrika Mashariki",
    "fr":       "Conseils médicaux — Afrique Occidentale/Haiti",
    "bn":       "চিকিৎসা নির্দেশিকা — বাংলাদেশ/ভারত",
    "tl":       "Gabay sa kalusugan — Pilipinas",
    "am":       "የጤና መመሪያ — ኢትዮጵያ",
    "ps":       "د روغتیا لارښود — افغانستان/پاکستان",
    "so":       "Hagaajinta caafimaadka — Soomaaliya",
    "pt":       "Orientação clínica — Moçambique/Angola/Brasil",
    "es":       "Orientación clínica — América Latina",
    "id":       "Panduan kesehatan — Indonesia/Malaysia",
    "yo":       "Itọsọna ilera — Naijiria/Benin/Togo",
    "ig":       "Nduzi ahụike — Naịjịrịa",
    "zu":       "Iseluleko sezempilo — Ningizimu Afrika",
    "ti":       "ምርሻን ሕሙም — ኤርትራ/ኢትዮጵያ",
    "my":       "ကျန်းမာရေး လမ်းညွှန် — မြန်မာ",
    "km":       "ការណែនាំសុខភាព — កម្ពុជា",
    "ne":       "स्वास्थ्य मार्गदर्शन — नेपाल",
}

TOOLTIPS = {
    "en": """
┌─────────────────────────────────────────────────────────┐
│                    HOW TO USE MEDI                      │
├────────────────┬────────────────────────────────────────┤
│ TYPE anything  │ Describe symptoms → Medi asks          │
│                │ follow-up questions → gives action     │
├────────────────┼────────────────────────────────────────┤
│ voice          │ Speak instead of typing. Medi listens  │
│                │ and responds in your language          │
├────────────────┼────────────────────────────────────────┤
│ image <path>   │ Analyze wound/rash photo               │
│                │ e.g: image C:\\photos\\wound.jpg        │
├────────────────┼────────────────────────────────────────┤
│ stats          │ Today's patient summary:               │
│                │ emergencies, referrals, home care      │
├────────────────┼────────────────────────────────────────┤
│ reset          │ Start fresh for a new patient          │
├────────────────┼────────────────────────────────────────┤
│ lang           │ Switch to a different language         │
├────────────────┼────────────────────────────────────────┤
│ quit           │ Exit Medi                              │
└────────────────┴────────────────────────────────────────┘
""",
    "ur-roman": """
┌─────────────────────────────────────────────────────────┐
│                  MEDI KAISE CHALAYEIN                   │
├────────────────┬────────────────────────────────────────┤
│ Kuch bhi type  │ Symptoms batao → Medi sawaal poochega  │
│                │ → phir clear action batayega           │
├────────────────┼────────────────────────────────────────┤
│ voice          │ Likhne ki bajaye bolein. Medi sunega   │
│                │ aur apni zaban mein jawab dega         │
├────────────────┼────────────────────────────────────────┤
│ image <path>   │ Zakhm/daane ki photo analyze karo      │
│                │ e.g: image C:\\photos\\zakhm.jpg        │
├────────────────┼────────────────────────────────────────┤
│ stats          │ Aaj ke mareez ka summary:              │
│                │ emergency, referral, ghar pe dekhbhal  │
├────────────────┼────────────────────────────────────────┤
│ reset          │ Naye mareez ke liye nai conversation   │
├────────────────┼────────────────────────────────────────┤
│ lang           │ Zaban tabdeel karo                     │
├────────────────┼────────────────────────────────────────┤
│ quit           │ Medi band karo                         │
└────────────────┴────────────────────────────────────────┘
""",
    "ur": """
┌─────────────────────────────────────────────────────────┐
│                   میڈی کیسے چلائیں                     │
├────────────────┬────────────────────────────────────────┤
│ کچھ بھی لکھیں  │ علامات بتائیں ← میڈی سوال پوچھے گا   │
│                │ پھر واضح ہدایت دے گا                  │
├────────────────┼────────────────────────────────────────┤
│ voice          │ بولیں — ٹائپ کی ضرورت نہیں            │
│                │ میڈی سنے گا اور اپنی زبان میں جواب دے │
├────────────────┼────────────────────────────────────────┤
│ image          │ زخم یا دانے کی تصویر تجزیہ کریں       │
├────────────────┼────────────────────────────────────────┤
│ stats          │ آج کے مریضوں کا خلاصہ دیکھیں          │
├────────────────┼────────────────────────────────────────┤
│ reset          │ نئے مریض کے لیے نئی گفتگو              │
├────────────────┼────────────────────────────────────────┤
│ lang           │ زبان تبدیل کریں                        │
├────────────────┼────────────────────────────────────────┤
│ quit           │ میڈی بند کریں                          │
└────────────────┴────────────────────────────────────────┘
""",
    "ha": """
┌─────────────────────────────────────────────────────────┐
│                YADDA AKE AMFANI DA MEDI                 │
├────────────────┬────────────────────────────────────────┤
│ Rubuta kome    │ Bayyana alamu → Medi zai tambaya        │
│                │ → sannan ya ba da umurni               │
├────────────────┼────────────────────────────────────────┤
│ voice          │ Yi magana maimakon rubuta               │
├────────────────┼────────────────────────────────────────┤
│ image          │ Dauki hoto na rauni ko kurji            │
├────────────────┼────────────────────────────────────────┤
│ stats          │ Duba takaitaccen bayani na yau          │
├────────────────┼────────────────────────────────────────┤
│ reset          │ Fara sabo don sabon majiyyaci           │
├────────────────┼────────────────────────────────────────┤
│ lang           │ Canza harshe                            │
├────────────────┼────────────────────────────────────────┤
│ quit           │ Rufe Medi                              │
└────────────────┴────────────────────────────────────────┘
""",
    "sw": """
┌─────────────────────────────────────────────────────────┐
│               JINSI YA KUTUMIA MEDI                     │
├────────────────┬────────────────────────────────────────┤
│ Andika chochote│ Elezea dalili → Medi atauliza maswali  │
│                │ → kisha atoa hatua                     │
├────────────────┼────────────────────────────────────────┤
│ voice          │ Sema badala ya kuandika                 │
├────────────────┼────────────────────────────────────────┤
│ image          │ Changanua picha ya jeraha au upele      │
├────────────────┼────────────────────────────────────────┤
│ stats          │ Ona muhtasari wa wagonjwa wa leo        │
├────────────────┼────────────────────────────────────────┤
│ reset          │ Anza upya kwa mgonjwa mpya              │
├────────────────┼────────────────────────────────────────┤
│ lang           │ Badilisha lugha                         │
├────────────────┼────────────────────────────────────────┤
│ quit           │ Funga Medi                             │
└────────────────┴────────────────────────────────────────┘
""",
    "fr": """
┌─────────────────────────────────────────────────────────┐
│               COMMENT UTILISER MEDI                     │
├────────────────┬────────────────────────────────────────┤
│ Tapez quelque  │ Decrivez symptomes → Medi pose des      │
│ chose          │ questions → donne une action claire    │
├────────────────┼────────────────────────────────────────┤
│ voice          │ Parlez au lieu de taper                │
├────────────────┼────────────────────────────────────────┤
│ image          │ Analysez une photo de plaie/eruption   │
├────────────────┼────────────────────────────────────────┤
│ stats          │ Resume des patients d aujourd hui      │
├────────────────┼────────────────────────────────────────┤
│ reset          │ Nouveau patient nouvelle conversation  │
├────────────────┼────────────────────────────────────────┤
│ lang           │ Changer de langue                      │
├────────────────┼────────────────────────────────────────┤
│ quit           │ Quitter Medi                           │
└────────────────┴────────────────────────────────────────┘
""",
    "es": """
┌─────────────────────────────────────────────────────────┐
│               COMO USAR MEDI                            │
├────────────────┬────────────────────────────────────────┤
│ Escribe algo   │ Describe sintomas → Medi pregunta       │
│                │ → luego da una accion clara            │
├────────────────┼────────────────────────────────────────┤
│ voice          │ Habla en vez de escribir               │
├────────────────┼────────────────────────────────────────┤
│ image          │ Analiza foto de herida/erupcion        │
├────────────────┼────────────────────────────────────────┤
│ stats          │ Resumen de pacientes de hoy            │
├────────────────┼────────────────────────────────────────┤
│ reset          │ Nuevo paciente nueva conversacion      │
├────────────────┼────────────────────────────────────────┤
│ lang           │ Cambiar idioma                         │
├────────────────┼────────────────────────────────────────┤
│ quit           │ Salir de Medi                          │
└────────────────┴────────────────────────────────────────┘
""",
    "pt": """
┌─────────────────────────────────────────────────────────┐
│               COMO USAR O MEDI                          │
├────────────────┬────────────────────────────────────────┤
│ Digite algo    │ Descreva sintomas → Medi pergunta       │
│                │ → depois da uma acao clara             │
├────────────────┼────────────────────────────────────────┤
│ voice          │ Fale em vez de digitar                 │
├────────────────┼────────────────────────────────────────┤
│ image          │ Analise foto de ferida/erupcao         │
├────────────────┼────────────────────────────────────────┤
│ stats          │ Resumo dos pacientes de hoje           │
├────────────────┼────────────────────────────────────────┤
│ reset          │ Novo paciente nova conversa            │
├────────────────┼────────────────────────────────────────┤
│ lang           │ Mudar idioma                           │
├────────────────┼────────────────────────────────────────┤
│ quit           │ Sair do Medi                           │
└────────────────┴────────────────────────────────────────┘
""",
}

GOODBYES = {
    "en": "Goodbye!",
    "ur-roman": "Khuda Hafiz!",
    "ur": "اللہ حافظ!",
    "hi": "अलविदा!",
    "ha": "Sai anjima!",
    "sw": "Kwaheri!",
    "fr": "Au revoir!",
    "bn": "বিদায়!",
    "tl": "Paalam!",
    "am": "ደህና ሁኑ!",
    "ps": "خداى پامان!",
    "so": "Nabad gelyo!",
    "pt": "Adeus!",
    "es": "Adios!",
    "id": "Selamat tinggal!",
}


def get_tooltip(lang_code: str) -> str:
    return TOOLTIPS.get(lang_code, TOOLTIPS["en"])


def get_prompt_symbol(lang_code: str) -> str:
    prompts = {
        "ur": "صحت کارکن",
        "ur-roman": "CHW",
        "hi": "स्वास्थ्य कार्यकर्ता",
        "ha": "Ma'aikaci",
        "sw": "Mfanyakazi",
        "fr": "Agent",
        "am": "Sehategna",
        "bn": "Swasthyakarmee",
        "yo": "Oluranlowo",
        "ig": "Onye oru",
        "zu": "Msebenzi",
        "es": "Agente",
        "pt": "Agente",
        "id": "Petugas",
        "tl": "Manggagawa",
        "so": "Shaqaale",
        "ps": "CHW",
        "ti": "Serahategna",
        "my": "CHW",
        "km": "CHW",
        "ne": "Swasthyakarmee",
    }
    return prompts.get(lang_code, "CHW")


def get_goodbye(lang_code: str) -> str:
    return GOODBYES.get(lang_code, "Goodbye!")


def show_language_menu():
    print("\n" + "=" * 62)
    print("  SELECT YOUR LANGUAGE / apni zaban select karein")
    print("=" * 62)
    for num, (name, code, _) in LANGUAGES.items():
        desc = LANG_DESCRIPTIONS.get(code, "")
        print(f"  [{num:>2}]  {name:<14} — {desc}")
    print("=" * 62)


def clean_response(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"Thinking Process:.*?\.\.\.done thinking\.", "", text, flags=re.DOTALL)
    text = re.sub(r"\*\*|\*|##|#", "", text)
    return text.strip()


def is_final_verdict(response: str) -> bool:
    verdict_keywords = [
        "home care", "refer", "emergency", "hospital",
        "ghar pe", "clinic", "foran", "immediately",
        "go to", "take to", "visit the",
    ]
    response_lower = response.lower()
    return any(keyword in response_lower for keyword in verdict_keywords)


def run_text_mode():
    print(BANNER)
    init_db()

    show_language_menu()
    while True:
        choice = input("\n  Enter number (1-22): ").strip()
        if choice in LANGUAGES:
            lang_name, lang_code, greeting = LANGUAGES[choice]
            break
        print("  Invalid. Enter 1-22.")

    print(f"\n  Language set: {lang_name}\n")
    print(greeting)
    print(get_tooltip(lang_code))

    prompt = get_prompt_symbol(lang_code)
    history = []

    while True:
        try:
            user_input = input(f"\n{prompt} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{get_goodbye(lang_code)}")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "quit":
            print(get_goodbye(lang_code))
            break

        elif cmd == "reset":
            reset()
            history = []
            print(f"\n{greeting}\n")

        elif cmd == "lang":
            show_language_menu()
            choice = input("\n  Enter number (1-22): ").strip()
            if choice in LANGUAGES:
                lang_name, lang_code, greeting = LANGUAGES[choice]
                prompt = get_prompt_symbol(lang_code)
                reset()
                history = []
                print(f"\n  Language set: {lang_name}\n")
                print(greeting)
                print(get_tooltip(lang_code))

        elif cmd == "stats":
            stats = get_stats()
            print(f"\n{'─'*35}")
            print(f"  Total Visits : {stats['total_visits']}")
            print(f"  Emergencies  : {stats['emergencies']}")
            print(f"  Referrals    : {stats['referrals']}")
            print(f"  Home Care    : {stats['home_care']}")
            print(f"{'─'*35}")

        elif cmd == "voice":
            print("\n  Listening...")
            user_input = listen()
            if not user_input or "unavailable" in user_input.lower():
                print("  Could not hear. Try again.")
                continue
            print(f"  Heard: {user_input}\n")
            result = run_agent(user_input, history)
            history = result["history"]
            response = clean_response(result["response"])
            speak(response)

            if is_final_verdict(response):
                severity = assess_severity(user_input)
                print(f"\n  [{severity['level']}] {severity['action']}")
                log_visit(
                    symptoms=user_input,
                    severity=severity["level"],
                    action=severity["action"],
                    language=lang_code,
                    tool_used=result.get("tool_used"),
                    response=response
                )
            else:
                log_visit(
                    symptoms=user_input,
                    severity="PENDING",
                    action="IN PROGRESS",
                    language=lang_code,
                    tool_used=result.get("tool_used"),
                    response=response
                )

        elif cmd.startswith("image"):
            parts = user_input.split(maxsplit=1)
            path = parts[1] if len(parts) > 1 else input("  Image path: ").strip()
            print("\n  Analyzing image...")
            result = analyze_image(path)
            result = clean_response(result)
            print(f"\nMedi: {result}")
            speak(result)

        else:
            result = run_agent(user_input, history)
            history = result["history"]
            response = clean_response(result["response"])

            if is_final_verdict(response):
                severity = assess_severity(user_input)
                print(f"\n  [{severity['level']}] {severity['action']}")
                log_visit(
                    symptoms=user_input,
                    severity=severity["level"],
                    action=severity["action"],
                    language=lang_code,
                    tool_used=result.get("tool_used"),
                    response=response
                )
            else:
                log_visit(
                    symptoms=user_input,
                    severity="PENDING",
                    action="IN PROGRESS",
                    language=lang_code,
                    tool_used=result.get("tool_used"),
                    response=response
                )


if __name__ == "__main__":
    _ = chat
    run_text_mode()
