#!/bin/bash
# Helper: pk <host> <curl-args...>  e.g. pk www.phantomkernel.htb /login
IP=154.57.164.73; PORT=31374
HOST="$1"; shift
curl -s -m 30 --resolve "$HOST:$PORT:$IP" "$@"
