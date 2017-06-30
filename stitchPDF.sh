#!/bin/bash

#mount proc /proc -t proc


#set -euo pipefail
IFS=$'\n\t'
cpus=$(nproc --all)


echo $1 $2 $3

echo $* > /tmp/stitchPDF

#export PYTHONPATH=/home/mq20151400/exporters/FAIMSScanner/

#echo ${2}ScanRecord/Files/$3
IFS=$'\n'

cd $2
#FIX
rm -rf pdf/$3
mkdir -p pdf/$3
cd pdf/$3


echo "Finding Identifier $3"

find ../../ -name "$3" -type d | xargs -I{} find {} -name "*.jpg" ! -name '.*' | sort -V 

#Brian plan. Copy jpgs in and rotate them first.

#find ../../ScanRecord/Files/$3 -name "*.jpg"| sort -V | awk -- 'BEGIN{ FS="[/.]+"} {print "convert " $0 " " ++count ".pnm"}' /dev/stdin | bash
find ../../ -name "$3" -type d | xargs -I{} find {} -name "*.jpg" ! -name '.*' | sort -V | awk -- 'BEGIN{ FS="[/.]+"} {print "convert \"" $0 "\" " ++count ".pnm"}' /dev/stdin | parallel --no-notice



echo "Scantailor"
parallel --no-notice "scantailor-cli --despeckle=normal --normalize-illumination --color-mode=black_and_white --dewarping=auto {} ./ ; rm {}" ::: $(find . -name "*.pnm" | sort -V)
rm -rf cache



echo "tiff2pdf"
parallel --no-notice "tiff2pdf -o '{.}.pdf' -z -u m -p 'A4' -F -c 'scanimage+unpaper+tiff2pdf+pdftk+imagemagick+tesseract+exactimage' {} ; rm {}" ::: $(find . -name "*.tif")





# for file in $(find . -name "*.pnm" | sort -V); do
# 	#echo $file
# 
# 	scantailor-cli --despeckle=normal --normalize-illumination --color-mode=black_and_white --dewarping=auto $file ./
# 	rm $file
# 	rm -rf cache
# done


#echo "tiff2pdf"
# for file in $(find . -name "*.tif" | sort -V); do
#	#echo $file
#	name=$(echo "$file" | cut -d'.' -f2)
#	name=".$name"
#
#	tiff2pdf -o "$name.pdf" -z -u m -p "A4" -F $name.tif	
#	rm $file	
#done
echo "pdf14"
pdf14=$(cat <<-'HereDoc'
mv {} {.}.bak;
pdftk {.}.bak dump_data > {.}.info;
pdftk {.}.bak cat output {.}.bk2 flatten;
convert -normalize -density 300 -depth 8 {.}.bk2 {.}.png;
tesseract -l eng -psm 1 {.}.png {} hocr 2> /dev/null;
TXT=$(echo {/.} | sed -e 's/_/./g;s/L/1/;s/R/2/')
tesseract -l eng -psm 1 {.}.png stdout >> $(printf "%03f_ENG.txt" $TXT) 2>/dev/null;
convert {.}.png {.}.jpg;
hocr2pdf -i {.}.jpg -s -o {.}.bk2 < {}.hocr 2> /dev/null;
pdftk {.}.bk2 update_info {.}.info output {} 2< /dev/null;
rm -f {.}.bak {.}.bk2 {.}.info {.}.png {.}.jpg {}.hocr;
HereDoc
)
parallel "$pdf14" ::: $(find . -name "*.pdf") 

#echo "pdf 1.4"
# for file in $(find . -name "*.pdf" | sort -V); do
# 	#echo $file
# 	name=$(basename "$file")
# 	name="${name%.*}"
# 
# 	#echo $name
# 	mv "$file" "$name.bak"
# 	pdftk "$name.bak" dump_data > $file.info
# 	pdftk "$name.bak" cat output "$name.bk2" flatten
# 
# 	convert -normalize -density 300 -depth 8 "$name.bk2" "$name.png"	
# 	tesseract -l eng -psm 1 "$name.png" "$file" hocr 2> /dev/null
# 	tesseract -l eng -psm 1 "$name.png" stdout >> "${3}ENG.txt" 2> /dev/null
# 
# 
# 	convert "$name.png" "$name.jpg"
# 	hocr2pdf -i "$name.jpg" -s -o "$name.bk2" < "$file.hocr" 2> /dev/null
# 
# 	pdftk "$name.bk2" update_info $file.info output "$name.OCR.pdf"
# 	rm -f "$name.bak" "$name.bk2" "$file.info"
# 	rm -f "$name.png" "$name.jpg" "$file.hocr"
# 
# done

mkdir -p stage2

echo "ENG.txt"
for file in $(find . -name "*.txt" | sort -g); do
    cat $file  >> "stage2/${3}_ENG.txt"
    rm $file
done

echo "listing preocr files"
find .

echo "preOCR.pdf"


pdfunite `find . -name "*.pdf"| sort -V` "stage2/${3}_preOCR.pdf"
#FIX
rm *.pdf
#convert `find ../../ScanRecord/Files/$3 -name "*.jpg"| sort -V` -page a4 "stage2/${3}.pdf"

mkdir jpg2pdf


#parallel --jobs $cpus 'convert {} -compress lzw -auto-orient jpg2pdf/{/.}.tiff' ::: $(find ../../ScanRecord/Files/$3 -name "*.jpg")

#for file in $(find "../../ScanRecord/Files/$3" -name "*.jpg" | sort -V  ); do
#        outfile="jpg2pdf/$(basename -s ".jpg" $file).tiff"
#        convert "$file" -compress lzw -auto-orient "$outfile"
#done

#for file in  $(find "jpg2pdf/" -name "*.tiff" | sort -V); do
#        tiffcp -a $file jpg2pdf/multi.tiff 2> /dev/null 
#done

#tiff2pdf -p A4 -F -j -q 90 -f -o "stage2/${3}_preoriginal.pdf" jpg2pdf/multi.tiff 

cd jpg2pdf
echo "ConTeXt"


imageDir=$(find ../../../ -name "$3" -type d ! -path "pdf" |tr '\n' ',')

if [ -z "$4" ]; then
	echo "no argument for orientation"
	orientation=90
	paper="landscape"
else
	echo "$4"
	orientation=$4
	if [ "$orientation" -eq "0" -o "$orientation" -eq "180" ]; then
		paper="portrait"
	else
		paper="landscape"
	fi
fi	





cat <<-HereDoc > "${3}.tex"
\enableregime [utf]
\mainlanguage [en]

\setuppapersize[A4,${paper}][A4,${paper}]



\setupexternalfigures[directory={${imageDir}}]

\setuplayout[
    backspace=0pt,
    topspace=0pt,
    header=0pt,
    footer=0pt,
%    width=\pagewidth,
%    height=\pageheight
    ]


\setuppagenumbering[location={}]

\starttext
HereDoc



find ../../../ -name "$3" -type d | xargs -I{} find {} -name "*.jpg" ! -name '.*' -print0 | sort -V -z  | xargs -I{} -0 echo  "\externalfigure[{}][width=\pagewidth,maxwidth=\pagewidth, maxheight=\pageheight, orientation=${orientation}]" >> "temp.tex"


for path in $(find ../../../ -name "$3" -type d); do
	echo "s#${path}/##g"
	sed -i "s#${path}/##g" temp.tex
done

cat temp.tex >> "${3}.tex"


echo "\stoptext" >> "${3}.tex"

context --purgeall --quiet --batchmode "${3}.tex"

ls

mv "${3}.tex" "../${3}_preoriginal.tex"

mv "${3}.pdf" "../stage2/${3}_preoriginal.pdf"


cd ..


#ls stage2/*


#FIX
rm -rf jpg2pdf

#mv stage2/* .


cp ../../$3.md stage2/
cp ../../$3.info stage2/
cd stage2

echo "finishing"

echo "" >> $3.info

pandoc -i $3.md -t ConTeXt -s -o "${3}cover.tex"
sed -i 's/\[letter\]/\[A4\]/g' "${3}cover.tex"

context "${3}cover.tex" --purgeall --quiet --silent --batchmode > /dev/null

pdfunite "${3}cover.pdf" "${3}_preoriginal.pdf" "../${3}_originalfull.pdf"
pdfunite "${3}cover.pdf" "${3}_preOCR.pdf" "../${3}_OCR.pdf"


#pdftk "${3}_originalfull.pdf" dump_data_utf8 output "${3}prefull".info 2>/dev/null
#sed -i '/^Info/d' "${3}prefull.info"
#cat "$3.info" "${3}prefull.info" > "${3}full.info"

#cat "${3}.info"
#echo "***"
#pdftk "${3}_originalfull.pdf" update_info_utf8 "${3}.info" output "../$3_original.pdf" 


# pdftk "${3}_OCRfull.pdf" dump_data > "${3}preOCRfull".info 2>/dev/null
# cat "${3}prefull.info"
# sed -i '/^Info/d' "${3}prefull.info"
# sed -i '/^Info/d' "${3}preOCRfull.info"
# cat "$3.info" "${3}prefull.info" > "${3}full.info"
# cat "$3.info" "${3}preOCRfull.info" > "${3}OCRfull.info"
# 
# cd ..
# 
# echo "eng"
# cat stage2/$3.md "stage2/${3}_ENG.txt" > "${3}_ENG.txt"
# echo $?
# 
# echo "orig"
# cat "stage2/${3}full.info"
# pdftk "stage2/${3}_originalfull.pdf" update_info_utf8 "stage2/${3}full.info" output "$3_original.pdf" 
# echo $?
# 
# echo "ocr"
# pdftk "stage2/${3}_OCRfull.pdf" update_info_utf8 "stage2/${3}OCRfull.info" output "$3_OCR.pdf" 
# echo $?
cd ..

cat stage2/$3.md "stage2/${3}_ENG.txt" > "${3}_ENG.txt"
#FIX
rm -rf stage2

echo "* ${3}"
ls | sed -e 's/^/    * /'


exit 0
