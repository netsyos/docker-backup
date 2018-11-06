#!/bin/bash
if [ -z "$CONFIG_SCRIPT" ]; then
    CONFIG_SCRIPT=/data/container_config/configure.sh
fi

if [ -x "$CONFIG_SCRIPT" ]; then
    echo "configure script found"
    # Control will enter here if $DIRECTORY exists.
    exec $CONFIG_SCRIPT
else
    echo "no configure script"
fi

echo "configure done"