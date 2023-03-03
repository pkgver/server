#!/bin/sh

file=$1

# cd ../nixpkgs

git config feature.manyFiles 1

git --no-pager log $2 --no-decorate --no-color --pretty=format:"%H" --name-only --follow -- $file |
    while read -r commit_hash && read -r path; do
        content=$(git show "$commit_hash:$path")
        if version=$(grep -oP 'version\s*=\s*"\K(.*?)(?=")' <<< "$content"); then
            echo "$commit_hash $version"
        else
            version=$(cut -c1-7 <<< $commit_hash)
            echo "$commit_hash $version"
        fi
        read -r _ # discard empty newline
    done
