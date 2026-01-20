import time
from decision_engine import process_input

def main():
    print("Rain taps softly against the windows.")
    print("Hanekawa is here.\n")

    state = {
        "mood": 0,
        "context": "rainy_home",
        "last_qa_id": None,
        "repeat_name_count": 0,
        "idle_seconds": 0,
        "last_input_time": time.time(),
        "turn": 0
    }

    while True:
        user_input = input("> ").strip()

        if user_input == "/status":
            print(f"[Mood: {state['mood']} | Turn: {state['turn']}]")
            continue

        if user_input == "/sleep":
            print("Hanekawa yawns and turns away.")

            break

        response, should_exit = process_input(user_input, state)
        print(response)

        if should_exit:
            break

if __name__ == "__main__":
    main()
