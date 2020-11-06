#!/bin/bash

set_environment () {

  echo " Set environment variables"

  # Here, define your installation paths, versions etc.
  gccversion="$(gcc -dumpversion)"
  BOOST="$1"
  INSTALLD="$2"
  VERSION="$3"
  TARBALL="$4"
  LOCAL=$INSTALLD

  # set SLC5 platform name:
  LCG_PLATFORM=i686
  if [[ "$(uname -m)" == "x86_64" ]] ; then
    LCG_PLATFORM=x86_64
  fi
}

run () {

  workd=$(pwd)

  echo " Unpack LHAPDF"
  tar xvzf $TARBALL



  echo " Enter LHAPDF6 directory"
  cd LHAPDF-${VERSION}/

  echo " Configure LHAPDF"
  LIBRARY_PATH=$LD_LIBRARY_PATH ./configure CXXFLAGS="-static-libstdc++" --prefix=$LOCAL --bindir=$LOCAL/bin --datadir=$LOCAL/share --libdir=$LOCAL/lib --disable-python --with-boost=$BOOST --enable-static

  echo " Compile LHAPDF6"
  LIBRARY_PATH=$LD_LIBRARY_PATH make

  echo " Install LHAPDF6"
  LIBRARY_PATH=$LD_LIBRARY_PATH make install

  echo "copy index and conf file"
  cd $INSTALLD
  index="$(find . -name 'pdfsets.index')"
  cp $index $INSTALLD/share/LHAPDF/
  conf="$(find . -name 'lhapdf.conf')"
  cp $conf $INSTALLD/share/LHAPDF/

#  echo " Get LHAPDF sets"
#  cd $INSTALLD/share/LHAPDF
#  wget --no-parent --recursive --level=1 -e robots=off -A.tar.gz -nd https://www.hepforge.org/archive/lhapdf/pdfsets/6.1/
#  ls -1 *.tar.gz | while read line; do tar xvfz $line; done

  echo " Finished LHAPDF6 installation"
  cd $workd

}

set_environment "$@"
run "$@"

