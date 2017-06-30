
sudo apt-get install spatialite-bin libimage-exiftool-perl imagemagick scantailor libtiff-tools pdftk tesseract-ocr exactimage poppler-utils pandoc parallel -y
sudo mkdir -p /home/ubuntu/.parallel
sudo touch /home/ubuntu/.parallel/will-cite
sudo mkdir -p /root/.parallel
sudo touch /root/.parallel/will-cite

sudo mkdir /usr/local/context
sudo chown ubuntu /usr/local/context
cd /usr/local/context
wget http://minimals.contextgarden.net/setup/first-setup.sh
sh first-setup.sh --modules=all


cat <<-HereDoc > "/home/ubuntu/.bashrc"
 export OSFONTDIR=~/.fonts:/usr/share/fonts                                                      
 export TEXROOT=/usr/local/context/tex                                         
 export PATH=/usr/local/context/tex/texmf-linux/bin:/usr/local/context/bin:$PATH
HereDoc