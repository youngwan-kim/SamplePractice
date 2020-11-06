#!/bin/bash

set_environment () {

  echo " Set environment variables"

  INSTALLPATH="$1"  
  TARBALL="$2"
  HEPMC2PATH="$3"
  HEPMC2INCLUDEPATH=$HEPMC2PATH/include
  GZIPPATH="$4"
  OPTIONALDEPENDENCES="$5"

}

run () {

  workd=$(pwd)

  echo " Unpack PYTHIA8"
  tar xvzf $TARBALL

  echo " Enter PYTHIA8 directory"
  local version="$(ls -1d pythia* | grep -v tgz | sed 's/pythia//g')"
  cd pythia${version}/

  echo " Configure PYTHIA8"
  make distclean
  configStr="./configure --prefix=$INSTALLPATH --with-hepmc2=$HEPMC2PATH --with-hepmc2-include=$HEPMC2INCLUDEPATH --with-gzip=$GZIPPATH $OPTIONALDEPENDENCES"
  echo "$configStr"
  $configStr

# Small fix for Pythia8.2 version. This is harmless to subsequent versions
  unamestr=`uname`
  echo $CXX
  if [[ "$unamestr" == 'Darwin' && "$CXX" != 'clang' ]]; then
	sed -i '' 's/-Qunused-arguments//g' Makefile.inc 
  fi

  echo " Compile PYTHIA8"
  make
  make install

  echo " Compile PYTHIA8 examples"
  cd $INSTALLPATH/share/Pythia8/examples
  ls -1 main*.cc | while read line
  do
    make "$(echo "$line" | sed "s,\.cc,,g")"  
  done

  echo " Finished LHAPDF installation"
  cd $workd

}

set_environment "$@"
run "$@"
