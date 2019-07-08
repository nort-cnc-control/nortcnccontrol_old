#!/usr/bin/env python3
import re

re_completed = re.compile(r"completed N:([0-9]+) Q:([0-9]+).*")
re_started = re.compile(r"started N:([0-9]+) Q:([0-9]+).*")
re_queued = re.compile(r"queued N:([0-9]+) Q:([0-9]+).*")
re_dropped = re.compile(r"dropped N:([0-9]+) Q:([0-9]+).*")
re_error = re.compile(r"error.*")
redebug = re.compile(r"debug.*")


def build_answer(cmd, Nid, Q):
    return {
        "result" : "ok",
        "event" : cmd,
        "action" : Nid,
        "slots" : Q,
    }

def parse_answer(data):
    try:
        ans = data.decode("ascii")
    except Exception as e:
        return {"result" : "error", "error" : str(e)}

    ans = str(ans).strip()
    print("Received answer: [%s], len = %i" % (ans, len(ans)))
    if ans == "Hello":
        print("Hello received")
        return {"result" : "ok", "event" : "init"}

    match = re_started.match(ans)
    if match != None:
        Nid = int(match.group(1))
        Q = int(match.group(2))
        print("Action %i started" % Nid)
        return build_answer("start", Nid, Q)

    match = re_completed.match(ans)
    if match != None:
        Nid = int(match.group(1))
        Q = int(match.group(2))
        print("Action %i completed" % Nid)
        return build_answer("complete", Nid, Q)

    match = re_queued.match(ans)
    if match != None:
        Nid = int(match.group(1))
        Q = int(match.group(2))
        print("Action %i queued" % Nid)
        return build_answer("queue", Nid, Q)

    match = re_dropped.match(ans)
    if match != None:
        Nid = int(match.group(1))
        Q = int(match.group(2))
        print("Action %i dropped" % Nid)
        return build_answer("drop", Nid, Q)

    match = re_error.match(ans)
    if match != None:
        return {"result" : "ok", "event" : "error", "msg" : ans}
            
    match = redebug.match(ans)
    if match != None:
        return {"result" : "ok", "event" : "debug", "msg" : ans}
            
    return {"result" : "error", "error" : "unknown answer", "value" : ans}
