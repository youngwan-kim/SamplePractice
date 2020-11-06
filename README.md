# SamplePractice
---
### Quick Setup
```
USER="$USER"
GITACCOUNT="$GITACCOUNT"

source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsrel CMSSW_10_6_4
cd CMSSW_10_6_4/src
cmsenv

git-cms-init
# complie
scram b -j 5

mkdir -p ${CMSSW_BASE}/src/Configuration
cd ${CMSSW_BASE}/src/Configuration
# you should fork from https://github.com/choij1589/SamplePractice to your repository first
git clone https://github.com/$GITACCOUNT/SamplePractice.git
git remote add origin https://github.com/$GITACCOUNT/SamplePractice.git
git remote add upstream https://github.com/choij1589/SamplePractice.git

# compile 2
scram b

cd ${CMSSW_BASE}/src/Configuration/SamplePractice

# run cmsDriver.py command
# from gridpack to GENSIM
NEVENT=$NEVENT	# e.g. NEVENT=2000
FRAGMENT=$FRAGMENT # e.g. FRAGMENT=DYm50_CP5
cmsDriver.py Configuration/SamplePractice/python/${FRAGMENT}_cff.py \
--python_filename config/${FRAGMENT}_cfg.py --eventcontent RAWSIM,LHE \
--customise Configuration/DataProcessing/Utils.addMonitoring \
--datatier GEN,LHE --fileout file:${FRAGMENT}.root --conditions 106X_mc2017_realistic_v6 \
--beamspot Realistic25ns13TeVEarly2017Collision --step LHE,GEN \
--geometry DB:Extended --era Run2_2017 \
--no_exec --mc -n $NEVENT

# run cmsRun command
cmsRun config/${FRAGMENT}_cff.py
```
