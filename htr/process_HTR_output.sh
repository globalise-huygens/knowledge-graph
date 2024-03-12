#!/bin/bash

if [ -z "$1" ]; then
    echo "No source folder provided!"
    exit 1
fi

if [ -z "$2" ]; then
    echo "No target folder provided!"
    exit 1
fi

if [ ! -d "$2" ]; then
    mkdir $2
fi

for tarfile in $1/*.tar.gz; do

    filename=$(basename -- "$tarfile")
    # strip .tar.gz
    inventoryname="${filename%.*.*}"
    
    echo "Processing" $filename

    # Extract to tmp folder
    mkdir -p $2/$inventoryname/tmp 
    tar -xzf $tarfile -C $2/$inventoryname/tmp

    # Recursively find all xml files
    for f in $(find $2/$inventoryname/tmp -name "*.xml"); do

        filename=$(basename -- "$f")
        bash edit_pagexml.sh $f $2/$inventoryname/$filename

    done

    # Remove tmp folder again
    rm -rf $2/$inventoryname/tmp

done
