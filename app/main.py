from __future__ import annotations

from dataclasses import dataclass

from app.core.function_caller import run_agent
from app.core.gemma_engine import reset
from app.utils.local_db import get_recent_visits, get_stats, init_db, log_visit


BANNER = """
+--------------------------------------------------------------+
|                        MediVoice CLI                         |
|    Offline AI support for frontline community health work    |
+--------------------------------------------------------------+
"""

HELP_TEXT = """
Commands
  help             Show this help
  voice            Record from microphone, then run triage
  image <path>     Analyze a wound/rash/burn image
  stats            Show local visit totals
  recent           Show recent local visits
  reset            Start a new patient conversation
  lang             Change language
  quit             Exit the CLI

Typing anything else sends it to Medi as patient context.
"""


@dataclass(frozen=True)
class LanguageOption:
    menu_key: str
    label: str
    code: str
    greeting: str
    hint: str


LANGUAGES: tuple[LanguageOption, ...] = (
    LanguageOption("1", "English", "en", "Hello. I am Medi. Tell me about your patient.", "Global default"),
    LanguageOption("2", "Roman Urdu", "ur-roman", "Assalam. Main Medi hoon. Mareez ke bare mein batayein.", "Pakistan and India"),
    LanguageOption("3", "Urdu", "ur", "Assalam. Main Medi hoon. Mareez ke bare mein batayein.", "Pakistan"),
    LanguageOption("4", "Hindi", "hi", "Namaste. Main Medi hoon. Mareez ke bare mein batayein.", "India"),
    LanguageOption("5", "Hausa", "ha", "Sannu. Ni ne Medi. Ka fada min game da majiyyaci.", "Nigeria and Niger"),
    LanguageOption("6", "Swahili", "sw", "Habari. Mimi ni Medi. Niambie kuhusu mgonjwa.", "East Africa"),
    LanguageOption("7", "French", "fr", "Bonjour. Je suis Medi. Parlez-moi du patient.", "West and Central Africa"),
    LanguageOption("8", "Bangla", "bn", "Hello. Ami Medi. Rogir kotha bolun.", "Bangladesh"),
    LanguageOption("9", "Soomaali", "so", "Salaam. Anigu waxaan ahay Medi. Ka waran bukaanka.", "Somalia"),
    LanguageOption("10", "Spanish", "es", "Hola. Soy Medi. Cuentame del paciente.", "Latin America"),
    LanguageOption("11", "Portuguese", "pt", "Ola. Sou Medi. Fale sobre o paciente.", "Lusophone regions"),
    LanguageOption("12", "Indonesian", "id", "Halo. Saya Medi. Ceritakan tentang pasien.", "Indonesia"),
)

LANGUAGE_BY_KEY = {option.menu_key: option for option in LANGUAGES}


def print_language_menu() -> None:
    print("Choose a language:")
    for option in LANGUAGES:
        print(f"  {option.menu_key}. {option.label:<11} - {option.hint}")


def choose_language() -> LanguageOption:
    while True:
        print_language_menu()
        selected = input("> ").strip()
        option = LANGUAGE_BY_KEY.get(selected)
        if option:
            return option
        print("Invalid option. Please choose one of the listed numbers.")


def parse_action_label(response: str) -> str:
    upper = response.upper()
    if upper.startswith("EMERGENCY:"):
        return "EMERGENCY"
    if upper.startswith("REFER TO CLINIC:"):
        return "REFER"
    if upper.startswith("HOME CARE:"):
        return "HOME CARE"
    return "FOLLOW_UP"


def print_stats() -> None:
    stats = get_stats()
    print(
        "Stats:"
        f" total={stats['total_visits']}"
        f" emergency={stats['emergencies']}"
        f" refer={stats['referrals']}"
        f" home_care={stats['home_care']}"
    )


def print_recent_visits() -> None:
    rows = get_recent_visits(5)
    if not rows:
        print("No visits logged yet.")
        return

    print("Recent visits:")
    for row in rows:
        print(
            f"- {row['timestamp']} | {row['language']} | {row['severity']} | "
            f"{row['action']} | {row['symptoms']}"
        )


def handle_agent_turn(
    message: str,
    history: list[dict],
    language: LanguageOption,
    *,
    image_used: bool = False,
    speak_back: bool = False,
) -> list[dict]:
    result = run_agent(message, history)
    response = result["response"]
    tool_used = result.get("tool_used")
    tool_result = result.get("tool_result")
    action = parse_action_label(response)

    print(f"Medi: {response}")
    if tool_used:
        print(f"Tool: {tool_used}")
    if tool_result:
        print(f"Tool result: {tool_result}")

    log_visit(
        symptoms=message,
        severity=action,
        action=action,
        language=language.label,
        tool_used=tool_used,
        response=response,
        image_used=image_used,
    )

    if speak_back:
        from app.core.voice_handler import speak

        speak(response)

    return result["history"]


def normalize_image_path(raw: str) -> str:
    path = raw.strip()
    if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
        return path[1:-1]
    return path


def image_command_path(command: str) -> str | None:
    if not command.lower().startswith("image "):
        return None
    return normalize_image_path(command[6:])


def greet(language: LanguageOption) -> None:
    print()
    print(BANNER)
    print(f"Language: {language.label}")
    print(language.greeting)
    print(HELP_TEXT.strip())
    print()


def main_loop() -> None:
    init_db()
    language = choose_language()
    from app.core.voice_handler import set_tts_language

    set_tts_language(language.code)
    history: list[dict] = []

    greet(language)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        lowered = user_input.lower()

        if lowered == "quit":
            print("Goodbye.")
            break

        if lowered == "help":
            print(HELP_TEXT.strip())
            continue

        if lowered == "stats":
            print_stats()
            continue

        if lowered == "recent":
            print_recent_visits()
            continue

        if lowered == "reset":
            history = []
            reset()
            print("Started a new patient conversation.")
            print(language.greeting)
            continue

        if lowered == "lang":
            language = choose_language()
            set_tts_language(language.code)
            history = []
            reset()
            print(f"Language switched to {language.label}.")
            print(language.greeting)
            continue

        if lowered == "voice":
            from app.core.voice_handler import listen

            transcript = listen()
            if not transcript:
                print("No voice input captured.")
                continue
            print(f"Heard: {transcript}")
            history = handle_agent_turn(
                transcript,
                history,
                language,
                speak_back=True,
            )
            continue

        image_path = image_command_path(user_input)
        if image_path is not None:
            from app.core.image_analyzer import analyze_image

            result = analyze_image(image_path)
            print(f"Medi: {result}")
            action = parse_action_label(result)
            log_visit(
                symptoms=f"image:{image_path}",
                severity=action,
                action=action,
                language=language.label,
                tool_used="image_triage",
                response=result,
                image_used=True,
            )
            continue

        history = handle_agent_turn(user_input, history, language)


if __name__ == "__main__":
    main_loop()
