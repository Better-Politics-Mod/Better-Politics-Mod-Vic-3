#!/bin/bash

source create-release-vdf.sh better-politics-mod steam_desc.txt &> /dev/null
echo $1
steamcmd +login $1 $2 +workshop_build_item $(realpath workshop.vdf) +quit