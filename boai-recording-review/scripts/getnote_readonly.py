"""Read-only Getnote adapter. Credentials come only from named process variables."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://openapi.biji.com/open/api/v1"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(path, params, client_id, api_key):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={
        "Authorization": api_key, "X-Client-ID": client_id, "Accept": "application/json"
    })
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as response:
        payload = json.load(response)
    if payload.get("success") is not True:
        raise ValueError("api_rejected_request")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("unexpected_data_shape")
    return data


def find_notes(fetch, query, start_date=None, end_date=None, max_pages=20):
    matches, seen_ids, seen_cursors = [], set(), set()
    cursor = None
    for page in range(1, max_pages + 1):
        data = fetch("/resource/note/list", {"cursor": cursor} if cursor else {})
        notes = data.get("notes")
        if not isinstance(notes, list):
            raise ValueError("unexpected_notes_shape")
        for note in notes:
            note_id = str(note.get("note_id") or note.get("id") or "")
            title = str(note.get("title") or "")
            created = str(note.get("created_at") or "")
            tags = [str(t.get("name", "")) for t in (note.get("tags") or []) if isinstance(t, dict)]
            haystack = (title + " " + " ".join(tags)).casefold()
            if any(word.casefold() not in haystack for word in query.split()):
                continue
            if start_date or end_date:
                try:
                    recorded = date.fromisoformat(created[:10])
                except ValueError:
                    raise ValueError("unrecognized_recording_date") from None
                if start_date and recorded < date.fromisoformat(start_date):
                    continue
                if end_date and recorded > date.fromisoformat(end_date):
                    continue
            if note_id and note_id not in seen_ids:
                matches.append({"id": note_id, "title": title, "created_at": created,
                                "note_type": note.get("note_type"), "tags": tags})
                seen_ids.add(note_id)
        if data.get("has_more") is False:
            return {"notes": matches, "pages": page, "complete": True}
        if data.get("has_more") is not True:
            raise ValueError("missing_pagination_status")
        next_cursor = data.get("next_cursor")
        if next_cursor is None or next_cursor == "":
            next_cursor = data.get("cursor")
        if next_cursor is None or next_cursor == "":
            return {"notes": matches, "pages": page, "complete": False, "reason": "missing_cursor"}
        cursor = str(next_cursor)
        if cursor in seen_cursors:
            return {"notes": matches, "pages": page, "complete": False, "reason": "repeated_cursor"}
        seen_cursors.add(cursor)
    return {"notes": matches, "pages": max_pages, "complete": False, "reason": "page_limit"}


def write_detail(data, output):
    if not isinstance(data.get("note"), dict):
        raise ValueError("note_detail_missing")
    with Path(output).open("x", encoding="utf-8") as stream:
        json.dump(data["note"], stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "search", "detail"])
    parser.add_argument("--client-id-env", default="GETNOTE_CLIENT_ID")
    parser.add_argument("--key-env", default="GETNOTE_API_KEY")
    parser.add_argument("--query", default="")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--note-id")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        for value in (args.start_date, args.end_date):
            if value:
                date.fromisoformat(value)
        if args.start_date and args.end_date and args.start_date > args.end_date:
            raise ValueError("invalid_date_range")
        if not 1 <= args.max_pages <= 100:
            raise ValueError("max_pages_out_of_range")
        if args.command == "search" and not (args.query.strip() or args.start_date or args.end_date):
            raise ValueError("course_query_or_date_required")
        if args.command == "detail" and not (args.note_id and args.output):
            raise ValueError("note_id_and_output_required")
        cid, key = os.environ.get(args.client_id_env), os.environ.get(args.key_env)
        if not cid or not key:
            raise ValueError("injected_credentials_unavailable")
        fetch = lambda path, params: request(path, params, cid, key)
        if args.command == "check":
            data = fetch("/resource/note/list", {})
            if not isinstance(data.get("notes"), list):
                raise ValueError("unexpected_notes_shape")
            result = {"ok": True, "status": "connection_verified"}
        elif args.command == "search":
            result = {"ok": True, **find_notes(fetch, args.query, args.start_date,
                                              args.end_date, args.max_pages)}
        else:
            write_detail(fetch("/resource/note/detail", {"id": args.note_id}), args.output)
            result = {"ok": True, "status": "detail_saved", "note_id": args.note_id}
    except urllib.error.HTTPError as error:
        result = {"ok": False, "status": "http_error", "http_status": error.code}
    except Exception as error:
        # Never expose server bodies, request headers, environment values, or exception text.
        allowed = {"api_rejected_request", "unexpected_data_shape", "unexpected_notes_shape",
                   "unrecognized_recording_date", "missing_pagination_status", "note_detail_missing",
                   "invalid_date_range", "max_pages_out_of_range", "course_query_or_date_required",
                   "note_id_and_output_required", "injected_credentials_unavailable"}
        status = str(error) if isinstance(error, ValueError) and str(error) in allowed else type(error).__name__
        result = {"ok": False, "status": status}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
