#!/usr/bin/env bash
# Task 2 - TicketFlow recon: login response body, case forms, endpoint discovery.
# Authorized HTB COAE exam, dedicated instance, in scope.
# Usage:  bash exam/scripts/tf_recon.sh
set -u

IP=154.57.164.73
PORT=31374
HOST=staging.phantomkernel.htb
BASE="http://$HOST:$PORT"
RES="--resolve $HOST:$PORT:$IP"

line(){ printf '\n========== %s ==========\n' "$1"; }

line "LOGIN POST body (r.hale/password) - see the actual error/response"
curl -s -i $RES -c /tmp/tf.jar -d "username=r.hale&password=password" \
     "$BASE/ticketflow/login" | head -40

line "RAW case SUP-2418 - forms / inputs / api / identity / sentiment hooks"
curl -s $RES "$BASE/ticketflow/support/cases/SUP-2418" \
  | grep -iEn 'form|action=|<input|<textarea|<button|api|identity|sentiment|packet|upload|comment|update|csrf|token' \
  | head -60

line "ENDPOINT PROBE"
for path in \
  /ticketflow/ /ticketflow/login /ticketflow/logout /ticketflow/dashboard \
  /ticketflow/cases /ticketflow/case /ticketflow/support /ticketflow/support/status \
  /ticketflow/support/new /ticketflow/support/cases /ticketflow/support/cases/SUP-2418/update \
  /ticketflow/support/cases/SUP-2418/comment /ticketflow/api /ticketflow/api/ \
  /ticketflow/api/health /ticketflow/api/cases /ticketflow/api/identitygate \
  /ticketflow/api/sentiment /ticketflow/identitygate /ticketflow/sentiment \
  /ticketflow/packet /ticketflow/packets /ticketflow/committee /ticketflow/archive \
  /ticketflow/review /ticketflow/analyst /ticketflow/admin /ticketflow/static/ \
  /ticketflow/robots.txt /robots.txt ; do
  code=$(curl -s -o /dev/null -w "%{http_code}" $RES "$BASE$path")
  size=$(curl -s -o /dev/null -w "%{size_download}" $RES "$BASE$path")
  printf "%-48s -> %s  (%s bytes)\n" "$path" "$code" "$size"
done

line "OTHER PUBLIC CASES (look for one that invites partner input)"
for c in SUP-2426 SUP-2433; do
  printf '\n--- %s ---\n' "$c"
  curl -s $RES "$BASE/ticketflow/support/cases/$c" \
    | grep -iEn 'form|action=|<textarea|<input|submit|update|comment|upload|packet' | head -20
done

echo
echo "[*] done."
