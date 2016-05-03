#!/bin/bash

#echo $1 $2 $3 $4

echo $* > /tmp/stitchPDF

#export PYTHONPATH=/home/mq20151400/exporters/FAIMSScanner/

#echo ${2}ScanRecord/Files/$3

cd $2
rm -rf pdf/$3
mkdir -p pdf/$3
cd pdf/$3

find ../../ScanRecord/Files/$3 -name "*.jpg"| sort -V | awk -- 'BEGIN{ FS="[/.]+"} {print "convert " $0 " " ++count ".pnm"}' /dev/stdin | bash
for file in $(find . -name "*.pnm" | sort -V); do
	#echo $file
	
	scantailor-cli --despeckle=normal --normalize-illumination --color-mode=black_and_white --dewarping=auto $file ./
	rm $file
	rm -rf cache
done


#echo "tiff2pdf"
for file in $(find . -name "*.tif" | sort -V); do
	#echo $file
	name=$(echo "$file" | cut -d'.' -f2)
	name=".$name"

	tiff2pdf -o "$name.pdf" -z -u m -p "A4" -F $name.tif	
	rm $file	
done


#echo "pdf 1.4"
for file in $(find . -name "*.pdf" | sort -V); do
	#echo $file
	name=$(basename "$file")
	name="${name%.*}"

	#echo $name
	mv "$file" "$name.bak"
	pdftk "$name.bak" dump_data > $file.info
	pdftk "$name.bak" cat output "$name.bk2" flatten

	convert -normalize -density 300 -depth 8 "$name.bk2" "$name.png"	
	tesseract -l eng -psm 1 "$name.png" "$file" hocr 2> /dev/null
	tesseract -l eng -psm 1 "$name.png" stdout >> "${3}ENG.txt" 2> /dev/null


	convert "$name.png" "$name.jpg"
	hocr2pdf -i "$name.jpg" -s -o "$name.bk2" < "$file.hocr" 2> /dev/null

	pdftk "$name.bk2" update_info $file.info output "$name.OCR.pdf"
	rm -f "$name.bak" "$name.bk2" "$file.info"
	rm -f "$name.png" "$name.jpg" "$file.hocr"

done

mkdir -p stage2

pdfunite `find . -name "*.pdf"| sort -V` "stage2/${3}OCR.pdf"
rm *.pdf
convert `find ../../ScanRecord/Files/$3 -name "*.jpg"| sort -V` -page a4 "stage2/${3}.pdf"
cp ../../$3.md stage2/
cp ../../$3.info stage2/
cd stage2
#echo $?
pandoc -i $3.md -t ConTeXt -s -o "${3}cover.tex"
sed -i 's/\[letter\]/\[A4\]/g' "${3}cover.tex"
#echo $?
context "${3}cover.tex" --purgeall --quiet --batchmode > /dev/null
#echo $?
pdfunite "${3}cover.pdf" "${3}.pdf" "${3}full.pdf"
pdfunite "${3}cover.pdf" "${3}OCR.pdf" "${3}OCRfull.pdf"
pdftk "${3}full.pdf" dump_data > "${3}prefull".info 2>/dev/null
pdftk "${3}OCRfull.pdf" dump_data > "${3}preOCRfull".info 2>/dev/null
sed -i '/^Info/d' "${3}prefull.info"
sed -i '/^Info/d' "${3}preOCRfull.info"
cat "$3.info" "${3}prefull.info" > "${3}full.info"
cat "$3.info" "${3}preOCRfull.info" > "${3}OCRfull.info"

cd ..

pdftk "stage2/${3}full.pdf" update_info_utf8 "stage2/$3full.info" output "$3.pdf" 2>/dev/null
pdftk "stage2/${3}OCRfull.pdf" update_info_utf8 "stage2/$3OCRfull.info" output "$3OCR.pdf" 2>/dev/null

rm -rf stage2
exit 0