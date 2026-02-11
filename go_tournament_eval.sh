#!/bin/bash

clear

display_mode=1

for mapId in {0..9}; do
	echo "Arena: $mapId"
    for initPos in True False; do
        python tetracomposibot.py config_Paintwars_eval "$mapId" "$initPos" "$display_mode"
    done
done
