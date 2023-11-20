#!/bin/bash  

XMLFILE=$1
TARGETFILE=$2

PREFIX="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"
HANDLE_LAYOUT="https://hdl.handle.net/10622/VMSCBR"
HANDLE_HTR="https://hdl.handle.net/10622/X2JZYY"

# Layout model
# Delete model data
xmlstarlet ed -N p=$PREFIX -d "//p:Metadata/p:MetadataItem[@type='processingStep' and @name='layout-analysis']/p:Labels/p:Label[@type='model']" $XMLFILE | 

# Replace model URI
xmlstarlet ed -N p=$PREFIX -u "//p:Metadata/p:MetadataItem[@type='processingStep' and @name='layout-analysis']/p:Labels/p:Label[@type='laypamodelremote']/@value" -v $HANDLE_LAYOUT |

# HTR-model
# Delete model data
xmlstarlet ed -N p=$PREFIX -d "//p:Metadata/p:MetadataItem[@type='processingStep' and @name='htr']/p:Labels/p:Label[@type='model']" |

# Replace model URI
xmlstarlet ed -N p=$PREFIX -u "//p:Metadata/p:MetadataItem[@type='processingStep' and @name='htr']/p:Labels/p:Label[@type='loghihtrmodelremote']/@value" -v $HANDLE_HTR |

# Metadata
# Add metadata element
xmlstarlet ed -N p=$PREFIX \
-s "//p:Metadata" -t elem -n MetadataItem -v "" \
-i "//MetadataItem" -t attr -n type -v "other" \
-i "//MetadataItem" -t attr -n name -v "dataset" \
-i "//MetadataItem" -t attr -n value -v "https://hdl.handle.net/10622/LVXSBW" \
-s "//MetadataItem" -t elem -n Labels -v "" \
-s "//Labels" -t elem -n Label -v "" \
-s "//Labels" -t elem -n Label -v "" \
-s "//Labels" -t elem -n Label -v "" \
-s "//Labels" -t elem -n Label -v "" \
-i "//Labels/Label[1]" -t attr -n value -v "VOC transcriptions v2 - GLOBALISE" \
-i "//Labels/Label[1]" -t attr -n type -v "name" \
-i "//Labels/Label[2]" -t attr -n value -v "Dataset in pagexml and txt format, including data card." \
-i "//Labels/Label[2]" -t attr -n type -v "description" \
-i "//Labels/Label[3]" -t attr -n value -v "https://globalise.huygens.knaw.nl/" \
-i "//Labels/Label[3]" -t attr -n type -v "creator" \
-i "//Labels/Label[4]" -t attr -n value -v "https://hdl.handle.net/10622/LVXSBW" \
-i "//Labels/Label[4]" -t attr -n type -v "url" |

# Text
# Remove PlainText elements
xmlstarlet ed -N p=$PREFIX -d "//p:PlainText" > $TARGETFILE