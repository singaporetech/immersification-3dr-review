#!/usr/bin/env bash
set -e

for f in /tmp/.X*-lock; do if [[ -f $f ]]; then echo "remove: $f"; sudo rm $f; fi done
for f in /tmp/.X11-unix/X*; do if [[ -a $f ]]; then echo "remove: $f"; sudo rm $f; fi done
startx -- :1 & sleep 1
x11vnc -nopw -display :1 -rfbport 5901 -forever -o .x11vnc.log -bg

exec "$@"