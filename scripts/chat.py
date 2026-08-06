import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.chatbot.rag import rag_service

def main():
    print("=" * 60)
    print(" 🌸 Lumeluxe AI Chatbot CLI - Streaming Engine")
    print("=" * 60)

    while True:
        try:
            query = input("\nYou: ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            result, sources_found = rag_service.ask_stream(query)

            print("\nBot: ", end="", flush=True)

            if isinstance(result, str):
                # Fallback static response string
                print(result)
            else:
                # Streamed token iteration
                for token in result:
                    print(token, end="", flush=True)
                print()

            print(f"\n[Sources Matched: {sources_found}]")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()