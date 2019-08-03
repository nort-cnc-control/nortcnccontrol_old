#!/usr/bin/env python3

def get_number(line):
    last = len(line) - 1
    has_dot = False
    sign = 1
    if line[0] == "-" or line[0] == "+":
        if line[0] == "-":
            sign = -1
        line = line[1:]

    for i in range(len(line)):
        if line[i] == ".":
            if not has_dot:
                has_dot = True
            else:
                break
        if not line[i].isdecimal():
            break
        last = i
    num = line[:last+1]
    try:
        val = int(num) * sign
    except:
        val = float(num) * sign
    return line[last+1:], val

def get_param(line):
    line = line.lstrip()
    if not line[0].isalpha():
        return line, None, None
    if line[1] != ":":
        return line, None, None
    tail = line[2:]
    param = line[0]
    tail, value = get_number(tail)
    if value is not None:
        return tail, param, value
    return line, None, None

def get_params(line):
    params = {}
    while len(line) > 0:
        line, param, value = get_param(line)
        if param is None:
            break
        params[param] = value
    return line, params

def build_answer(cmd, Nid, Q, params):
    return {
        "result" : "ok",
        "event" : cmd,
        "action" : Nid,
        "slots" : Q,
        "response" : params
    }

def parse_answer(data):
    ans = str(data).strip()
    if ans == "Hello":
        #print("Hello received")
        return {"result" : "ok", "event" : "init"}

    if ans.startswith("started"):
        _, params = get_params(ans[7:])
        Nid = params["N"]
        Q = params["Q"]
        #print("Action %i started" % Nid)
        return build_answer("start", Nid, Q, params)

    if ans.startswith("completed"):
        _, params = get_params(ans[9:])
        Nid = params["N"]
        Q = params["Q"]
        #print("Action %i started" % Nid)
        return build_answer("complete", Nid, Q, params)

    if ans.startswith("queued"):
        _, params = get_params(ans[6:])
        Nid = params["N"]
        Q = params["Q"]
        #print("Action %i started" % Nid)
        return build_answer("queue", Nid, Q, params)

    if ans.startswith("dropped"):
        _, params = get_params(ans[7:])
        Nid = params["N"]
        Q = params["Q"]
        #print("Action %i started" % Nid)
        return build_answer("drop", Nid, Q, params)

    if ans.startswith("error"):
        return {"result" : "ok", "event" : "error", "msg" : ans[5:]}

    if ans.startswith("debug"):
        return {"result" : "ok", "event" : "debug", "msg" : ans[5:]}

    return {"result" : "error", "error" : "unknown answer", "value" : ans}

if __name__ == "__main__":
    resp = "completed N:8 Q:8"
    print(parse_answer(resp))
