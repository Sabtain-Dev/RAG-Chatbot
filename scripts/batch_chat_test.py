"""Run chatbot questions from JSON and append every response to a text report."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run automated Lumeluxe chatbot questions and save responses."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "tests" / "chatbot_questions.json",
        help="JSON file containing questions or workflows.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "chatbot_test_results.txt",
        help="Text report to append results to.",
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="API base URL.")
    parser.add_argument("--timeout", type=float, default=120, help="Request timeout in seconds.")
    parser.add_argument("--delay", type=float, default=0, help="Seconds to wait between requests.")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop after the first failed request.")
    return parser.parse_args()


def load_cases(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return [
            item if isinstance(item, dict) else {"message": item}
            for item in data
        ]
    if isinstance(data, dict) and isinstance(data.get("cases"), list):
        return data["cases"]
    raise ValueError("Input JSON must be a list or an object containing a 'cases' list.")


def append_result(file, result: dict) -> None:
    file.write("\n" + "=" * 80 + "\n")
    file.write(f"[{result['timestamp']}] {result['id']} | {result['category']}\n")
    file.write(f"Question: {result['question']}\n")
    file.write(f"Session: {result.get('session_id', '(none)')}\n")
    file.write(f"HTTP status: {result['status']}\n")
    file.write(f"Sources found: {result.get('sources_found', '(unknown)')}\n")
    file.write("Answer:\n")
    file.write(result["answer"].rstrip() + "\n")
    file.flush()


class ApiClient:
    def post(self, url: str, payload: dict, timeout: float) -> tuple[int, dict]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {error.code}: {details}") from error


def run_case(
    client: ApiClient,
    base_url: str,
    case: dict,
    sessions: dict[str, str],
    timeout: float,
) -> dict:
    question = str(case.get("message", "")).strip()
    if not question:
        raise ValueError("Every case must contain a non-empty 'message'.")

    session_name = case.get("session")
    session_id = None
    if session_name:
        session_id = sessions.setdefault(session_name, str(uuid.uuid4()))

    if case.get("reset_before"):
        if not session_id:
            raise ValueError("'reset_before' requires a named 'session'.")
        reset_status, _ = client.post(
            f"{base_url}/chat/reset",
            {"session_id": session_id},
            timeout,
        )
        if reset_status >= 400:
            raise RuntimeError(f"HTTP {reset_status} while resetting session")

    payload = {"message": question}
    if session_id:
        payload["session_id"] = session_id

    status, body = client.post(f"{base_url}/chat", payload, timeout)
    if status >= 400:
        raise RuntimeError(f"HTTP {status} while sending chat request")
    returned_session_id = body.get("session_id")
    if session_name and returned_session_id:
        sessions[session_name] = returned_session_id

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "id": case.get("id", "unnamed"),
        "category": case.get("category", "general"),
        "question": question,
        "session_id": returned_session_id or session_id,
        "status": status,
        "sources_found": body.get("sources_found"),
        "answer": str(body.get("answer", "(response did not contain an answer)")),
    }


def main() -> int:
    args = parse_args()
    cases = load_cases(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sessions: dict[str, str] = {}
    passed = 0
    failed = 0

    client = ApiClient()
    with args.output.open("a", encoding="utf-8") as report:
        report.write(f"\n\nBatch started: {datetime.now().isoformat(timespec='seconds')}\n")
        report.write(f"Input: {args.input}\nAPI: {args.url}\nCases: {len(cases)}\n")
        report.flush()

        for number, case in enumerate(cases, start=1):
            case_id = case.get("id", f"case-{number}")
            try:
                result = run_case(client, args.url.rstrip("/"), case, sessions, args.timeout)
                append_result(report, result)
                passed += 1
                print(f"[{number}/{len(cases)}] {case_id}: OK")
            except Exception as error:
                failed += 1
                result = {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "id": case_id,
                    "category": case.get("category", "general"),
                    "question": case.get("message", ""),
                    "session_id": sessions.get(case.get("session"), "(none)"),
                    "status": "ERROR",
                    "sources_found": "(unknown)",
                    "answer": f"Request failed: {type(error).__name__}: {error}",
                }
                append_result(report, result)
                print(f"[{number}/{len(cases)}] {case_id}: ERROR - {error}", file=sys.stderr)
                if args.stop_on_error:
                    break
            if args.delay:
                time.sleep(args.delay)

        report.write("\n" + "=" * 80 + "\n")
        report.write(f"Finished: {datetime.now().isoformat(timespec='seconds')}\n")
        report.write(f"Completed: {passed}; Errors: {failed}\n")

    print(f"Completed: {passed}; Errors: {failed}")
    print(f"Results appended to: {args.output}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())