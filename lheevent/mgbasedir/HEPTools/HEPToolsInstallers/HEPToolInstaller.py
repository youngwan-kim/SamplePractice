#! /usr/bin/env python

__author__ = 'Valentin Hirschi'
__email__  = "valentin.hirschi[at]gmail[dot]com"

import sys
import os
import subprocess
import shutil
import tarfile
import tempfile
import glob
pjoin = os.path.join


_lib_extensions = ['a']
if sys.platform == "darwin":
   _lib_extensions.append('dylib')
else:
   _lib_extensions.append('so')

_HepTools = {'hepmc':
               {'install_mode':'Default',
                'version':       '2.06.09',
                'tarball':      ['online','http://lcgapp.cern.ch/project/simu/HepMC/download/HepMC-%(version)s.tar.gz'],
                'mandatory_dependencies': [],
                'optional_dependencies' : [],
                'libraries' : ['libHepMC.%(libextension)s'],
                'install_path':  '%(prefix)s/hepmc/'},
             'boost':
               {'install_mode':'Default',
                'version':       '1.59.0',
                'tarball':      ['online','http://sourceforge.net/projects/boost/files/boost/1.59.0/boost_1_59_0.tar.gz'],
                'mandatory_dependencies': [],
                'optional_dependencies' : [],
                'libraries' : ['libboost_system-mt.%(libextension)s','libboost_system.%(libextension)s'],
                'install_path':  '%(prefix)s/boost/'},
             'pythia8':
               {'install_mode':'Default',
                'version':       '82151',
# Official version
#                'tarball':      ['online','http://home.thep.lu.se/~torbjorn/pythia8/pythia8210.tgz'],
# Development version necessary for the Mg5_aMC_PY8_interface
                'tarball':      ['online','http://slac.stanford.edu/~prestel/pythia82151.tar.gz'],
                # We put zlib mandatory because we are not going to unzip .lhe files in MG5_aMC when passing them to PY8.
                'mandatory_dependencies': ['hepmc','zlib'],
                # Dependency lhapdf, without version specification means this installer will try linking against the most
                # recent version
                'optional_dependencies' : ['lhapdf'],
                'libraries' : ['libpythia8.%(libextension)s'],
                'install_path':  '%(prefix)s/pythia8/'},
             'lhapdf6':
               {'install_mode':'Default',
                'version':       '6.1.5',
                'tarball':      ['online','http://www.hepforge.org/archive/lhapdf/LHAPDF-%(version)s.tar.gz'],
                'mandatory_dependencies': ['boost'],
                'optional_dependencies' : [],
                'libraries' : ['libLHAPDF.%(libextension)s'],
                'install_path':  '%(prefix)s/lhapdf6/'},
             'lhapdf5':
               {'install_mode':'Default',
                'version':       '5.9.0',
                'tarball':      ['online','http://www.hepforge.org/archive/lhapdf/lhapdf-%(version)s.tar.gz'],
                'mandatory_dependencies': [],
                'optional_dependencies' : [],
                'libraries' : ['libLHAPDF.%(libextension)s'],
                'install_path':  '%(prefix)s/lhapdf5/'},
             'zlib':
               {'install_mode':'Default',
                'version':       '1.2.8',
                'tarball':      ['online','http://zlib.net/zlib-%(version)s.tar.gz'],
                'mandatory_dependencies': [],
                'optional_dependencies' : [],
                'libraries' : ['libz.%(libextension)s','libz.1.%(libextension)s',
                               'libz.1.2.8.%(libextension)s'],
                'install_path':  '%(prefix)s/zlib/'},
              'mg5amc_py8_interface':
               {'install_mode':'Default',
                'version':       '1.0',
#                'tarball':      ['online','http://madgraph.phys.ucl.ac.be/Downloads/MG5aMC_PY8_interface.tar.gz'],
                'tarball':      ['online','TO_BE_DEFINED_BY_INSTALLER'],
                'mandatory_dependencies': ['pythia8'],
                'optional_dependencies' : [],
                'libraries' : ['MG5aMC_PY8_interface'],
                'install_path':  '%(prefix)s/MG5aMC_PY8_interface/'},
               'ninja':
               {'install_mode':'Default',
                'version':       '1.1 (not semantic)',
                'tarball':      ['online','https://bitbucket.org/peraro/ninja/downloads/ninja-latest.tar.gz'],
                'mandatory_dependencies': ['oneloop'],
                'optional_dependencies' : [],
                'libraries' : ['libninja.%(libextension)s'],
                'install_path':  '%(prefix)s/ninja/'},
               'oneloop':
               {'install_mode':'Default',
                'version':       '3.6',
                'tarball':      ['online','http://helac-phegas.web.cern.ch/helac-phegas/tar-files/OneLOop-%(version)s.tgz'],
                'mandatory_dependencies': [],
                'optional_dependencies' : [],
                'libraries' : ['libavh_olo.a'],
                'install_path':  '%(prefix)s/oneloop/'}
            }

_cwd             = os.getcwd()
_installers_path = os.path.abspath(os.path.dirname(os.path.realpath( __file__ )))
_cpp             = 'g++'
_gfortran        = 'gfortran'
_prefix          = pjoin(_cwd,'HEPTools')
_overwrite_existing_installation = False
# MG5 path, can be used for the installation of mg5amc_py8_interface
_mg5_path        = None
_cpp_standard_lib= '-lstdc++'

if len(sys.argv)>1 and sys.argv[1].lower() not in _HepTools.keys():
    print "HEPToolInstaller does not support the installation of %s"%sys.argv[1]
    sys.argv[1] = 'help'

if len(sys.argv)<2 or sys.argv[1]=='help': 
    print """
./HEPToolInstaller <target> <options>"
     Possible values and meaning for the various <options> are:
           
     |           option           |    value           |                          meaning
     -============================-====================-===================================================
     | <target>                   | Any <TOOL>         | Which HEPTool to install
     | --prefix=<path>            | install root path  | Specify where to install target and dependencies
     | --force                    | -                  | Overwrite existing installation if necessary
     | --fortran_compiler=<path>  | path to gfortran   | Specify fortran compiler
     | --cpp_compiler=<path>      | path to g++        | Specify C++ compiler
     | --cpp_standard_lib=<lib>   | -lc++ or -lstdc++  | Specify which C++ standard library the compiler links to
     | --mg5_path=<path>          | path to MG5        | Specify what is the MG5 distribution invoking this
     | --with_<DEP>=<DepMode>     | <path>             | Use the specified path for dependency DEP
     |                            | Default            | Link against DEP if present otherwise install it
     |                            | OFF                | Do not link against dependency DEP
     | --<DEP>_tarball=<path>     | A path to .tar.gz  | Path of the tarball to be used if DEP is installed

     <TOOL> and <DEP> can be any of the following:\n        %s\n
Example of usage:
    ./HEPToolInstaller.py pythia8 --prefix=~/MyTools --with_lhapdf6=OFF --pythia8_tarball=~/MyTarball.tar.gz
"""%', '.join(_HepTools.keys())
    sys.exit(9)

target_tool = sys.argv[1].lower()

# Make sure to set the install location of all other tools than the target to 'default'. Meaning that they
# will be installed if not found.
for tool in _HepTools:
    if tool==target_tool:
        continue
    _HepTools[tool]['install_path']='default'

available_options = ['--prefix','--fortran_compiler','--cpp_compiler','--gfortran_compiler','--force','--mg5_path','--cpp_standard_lib']+\
                    ['--%s_tarball'%tool for tool in _HepTools.keys()]+\
                    ['--with_%s'%tool for tool in _HepTools.keys()]

# Recall input command for logfiles
print "Installer HEPToolInstaller.py is now processing the following command:"
print "   %s"%' '.join(sys.argv)

# Now parse the options
for user_option in sys.argv[2:]:
    try:
        option, value = user_option.split('=')
    except:
        option = user_option
        value  = None 
    if option not in available_options:
        print "Option '%s' not reckognized."%option
        sys.exit(9)
    if option=='--force':
        _overwrite_existing_installation = True
    if option=='--prefix':
        if not os.path.isdir(value):
            print "Creating root directory '%s'."%os.path.abspath(value)
            os.mkdir(os.path.abspath(value))
        _prefix = os.path.abspath(value)
    elif option=='--fortran_compiler':
        _gfortran = value
    elif option=='--cpp_compiler':
        _cpp = value
    elif option=='--cpp_standard_lib':
        if value not in ['-lc++','-lstdc++']:
            print "ERROR: Option '--cpp_standard_lib' must be either '-lc++' or '-libstdc++', not '%s'."%value
            sys.exit(9)
        _cpp_standard_lib = value
    elif option=='--mg5_path':
        _mg5_path = value
    elif option.startswith('--with_'):
        _HepTools[option[7:]]['install_path'] = value if value!='OFF' else None
    elif option.endswith('_tarball'):
        access_mode = 'online' if '//' in value else 'local'
        if access_mode=='local':
            value = os.path.abspath(value)
        _HepTools[option[2:-8]]['tarball'] = [access_mode, value]

# Apply substitutions if necessary:
for tool in _HepTools:
    if not _HepTools[tool]['install_path'] is None:
        _HepTools[tool]['install_path']=_HepTools[tool]['install_path']%{'prefix':_prefix}
    if _HepTools[tool]['tarball'][0]=='online':
        _HepTools[tool]['tarball'][1]=_HepTools[tool]['tarball'][1]%{'version':_HepTools[tool]['version']}
    
    new_libs = []
    for lib in _HepTools[tool]['libraries']:
        for libext in _lib_extensions:
            if lib%{'libextension':libext} not in new_libs:
                new_libs.append(lib%{'libextension':libext})
    _HepTools[tool]['libraries'] = new_libs

# Make sure it is not already installed, but if the directory is empty, then remove it
if os.path.isdir(pjoin(_prefix,target_tool)):
    if os.listdir(pjoin(_prefix,target_tool)) in [[],['%s_install.log'%target_tool]]:
        shutil.rmtree(pjoin(_prefix,target_tool))
    else:
        if not _overwrite_existing_installation:
            print "The specified path '%s' already contains an installation of tool '%s'."%(_prefix,target_tool)
            print "Rerun the HEPToolInstaller.py script again with the option '--force' if you want to overwrite it."
            sys.exit(66)
        else:
            print "Removing existing installation of tool '%s' in '%s'."%(target_tool,_prefix)
            shutil.rmtree(pjoin(_prefix,target_tool))

# TMP_directory (designed to work as with statement) and go to it
class TMP_directory(object):
    """create a temporary directory, goes to it, and ensure this one to be cleaned.
    """

    def __init__(self, suffix='', prefix='tmp', dir=None):
        self.nb_try_remove = 0
        import tempfile   
        self.path = tempfile.mkdtemp(suffix, prefix, dir)
        self.orig_path = os.getcwd()
        os.chdir(os.path.abspath(self.path))
    
    def __exit__(self, ctype, value, traceback ):
        os.chdir(self.orig_path)
        #True only for debugging:
        if False and isinstance(value, Exception):
            print "Directory %s not cleaned. This directory can be removed manually" % self.path
            return False
        try:
            shutil.rmtree(self.path)
        except OSError:
            import time
            self.nb_try_remove += 1
            if self.nb_try_remove < 3:
                time.sleep(10)
                self.__exit__(ctype, value, traceback)
            else:
                logger.warning("Directory %s not completely cleaned. This directory can be removed manually" % self.path)
        
    def __enter__(self):
        return self.path

def test_cpp_compiler(options):
    """ Try to compile a dummy c++ program to test whether the compiler support the options specified
    in argument."""

    support_it = False
    try:
        tmp_dir = tempfile.mkdtemp()
        open(pjoin(tmp_dir,'test_cpp_compiler.cc'),'w').write(
"""#include <iostream>

int main()
{
  std::cout << "Hello World!";
}
""")
        cpp_tester = [_cpp,]+options+['test_cpp_compiler.cc','-o','test_cpp_compiler']
        p = subprocess.Popen(cpp_tester, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=tmp_dir)
        output, error = p.communicate()
        support_it = (p.returncode == 0)
        # clean-up of the temporary file
        shutil.rmtree(tmp_dir)
    except Exception:
        try:
            shutil.rmtree(tmp_dir)
        except:
            pass
        pass
    return support_it

#==================================================================================================
# Now define the installation function
#==================================================================================================
def install_zlib(tmp_path):
    """Installation operations for zlib"""
    zlib_log = open(pjoin(_HepTools['zlib']['install_path'],"zlib_install.log"), "w")
    subprocess.call([pjoin(_installers_path,'installZLIB.sh'),
                     _HepTools['zlib']['install_path'],
                     _HepTools['zlib']['version'],
                     _HepTools['zlib']['tarball'][1]], 
                    stdout=zlib_log,
                    stderr=zlib_log)
    zlib_log.close()

def install_hepmc(tmp_path):
    """Installation operations for hepmc""" 
    hepmc_log = open(pjoin(_HepTools['hepmc']['install_path'],"hepmc_install.log"), "w")
    subprocess.call([pjoin(_installers_path,'installHEPMC2.sh'),
                     _HepTools['hepmc']['install_path'],
                     _HepTools['hepmc']['version'],
                     _HepTools['hepmc']['tarball'][1]],
                    stdout=hepmc_log,
                    stderr=hepmc_log)
    hepmc_log.close()

def install_boost(tmp_path):
    """Installation operations for boost"""
    boost_log = open(pjoin(_HepTools['boost']['install_path'],"boost_install.log"), "w")
    subprocess.call([pjoin(_installers_path,'installBOOST.sh'),
                     _HepTools['boost']['install_path'],
                     _HepTools['boost']['version'],
                     _HepTools['boost']['tarball'][1]],
                    stdout=boost_log,
                    stderr=boost_log)
    boost_log.close()

def install_oneloop(tmp_path):
    """Installation operations for OneLOop"""
    oneloop_log = open(pjoin(_HepTools['oneloop']['install_path'],"oneloop_install.log"), "w")
    subprocess.call([pjoin(_installers_path,'installOneLOop.sh'),
                     _HepTools['oneloop']['install_path'],
                     _HepTools['oneloop']['version'],
                     _HepTools['oneloop']['tarball'][1]],
                    stdout=oneloop_log,
                    stderr=oneloop_log)
    oneloop_log.close()

def install_ninja(tmp_path):
    """Installation operations for Ninja"""

    # Test whether the c++ compiler supports the -stdlib=libstdc++ option.
    # Typically clang++ supports it but not g++ which links to it by default anyway.
    cxx_flags = ['-O2']
    for flag in ['-fcx-fortran-rules','-fno-exceptions','-fno-rtti']:
        if test_cpp_compiler([flag]):
            cxx_flags.append(flag)

    ninja_log = open(pjoin(_HepTools['ninja']['install_path'],"ninja_install.log"), "w")
    subprocess.call([pjoin(_installers_path,'installNinja.sh'),
                     _HepTools['ninja']['install_path'],
                     _HepTools['ninja']['tarball'][1],
                     _HepTools['oneloop']['install_path'],
                     ' '.join(cxx_flags),_cpp_standard_lib], 
                    stdout=ninja_log,
                    stderr=ninja_log)
    ninja_log.close()

def install_lhapdf6(tmp_path):
    """Installation operations for lhapdf6"""
    lhapdf6_log = open(pjoin(_HepTools['lhapdf6']['install_path'],"lhapdf6_install.log"), "w")
    subprocess.call([pjoin(_installers_path,'installLHAPDF6.sh'),
                     _HepTools['boost']['install_path'],
                     _HepTools['lhapdf6']['install_path'],
                     _HepTools['lhapdf6']['version'],
                     _HepTools['lhapdf6']['tarball'][1]],
                    stdout=lhapdf6_log,
                    stderr=lhapdf6_log)
    lhapdf6_log.close()

def install_lhapdf5(tmp_path):
    """Installation operations for lhapdf5"""
    lhapdf5_log = open(pjoin(_HepTools['lhapdf5']['install_path'],"lhapdf5_install.log"), "w")
    subprocess.call([pjoin(_installers_path,'installLHAPDF5.sh'),
                     _HepTools['lhapdf5']['install_path'],
                     _HepTools['lhapdf5']['version'],
                     _HepTools['lhapdf5']['tarball'][1]],
                    stdout=lhapdf5_log,
                    stderr=lhapdf5_log)
    lhapdf5_log.close()

def install_mg5amc_py8_interface(tmp_path):
    """ Installation operations for the mg5amc_py8_interface"""
    
    # Extract the tarball
    tar = tarfile.open(_HepTools['mg5amc_py8_interface']['tarball'][1],)
    tar.extractall(path=_HepTools['mg5amc_py8_interface']['install_path'])
    tar.close()

    # Setup the options: the pythia8 path is mandatory. The MG5 on is optimal an only necessary
    # so as to indicate which version of MG5 was present on install.
    options = [_HepTools['pythia8']['install_path']]
    if not _mg5_path is None:
        options.append(_mg5_path)

    # Run the installation script
    mg5amc_py8_interface_log = open(pjoin(_HepTools['mg5amc_py8_interface']['install_path'],"mg5amc_py8_interface_install.log"), "w")
    subprocess.call([pjoin(_HepTools['mg5amc_py8_interface']['install_path'],'compile.py')]+options, 
                    stdout=mg5amc_py8_interface_log,
                    stderr=mg5amc_py8_interface_log)
    mg5amc_py8_interface_log.close()

def install_pythia8(tmp_path):
    """Installation operations for pythia8"""
    
    # Setup optional dependencies
    optional_dependences = []
    for dep in _HepTools['pythia8']['optional_dependencies']:
        if dep=='lhapdf6':
            optional_dependences.append('--with-lhapdf6=%s'%_HepTools['lhapdf6']['install_path'])
            optional_dependences.append('--with-lhapdf6-plugin=LHAPDF6.h')
            optional_dependences.append('--with-boost=%s'%_HepTools['boost']['install_path'])
        if dep=='lhapdf5':
            optional_dependences.append('--with-lhapdf5=%s'%_HepTools['lhapdf5']['install_path'])

    # Check whether hepmc was hacked to support named weights
    hepmc_named_weight_support = False
    try:
        tmp_dir = tempfile.mkdtemp()
        shutil.copyfile(pjoin(_installers_path,'test-hepmc2hack.cc'),
                        pjoin(tmp_dir,'test-hepmc2hack.cc'))
        hepmc_tester = [_cpp, 'test-hepmc2hack.cc','-o','test-hepmchack',
                       '-I%s'%pjoin(_HepTools['hepmc']['install_path'],'include'),
                       '-L%s'%pjoin(_HepTools['hepmc']['install_path'],'lib'),
                       '-lHepMC']
        p = subprocess.Popen(hepmc_tester, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=tmp_dir)
        output, error = p.communicate()
        hepmc_named_weight_support = (p.returncode == 0)
        # clean-up of the temporary file
        shutil.rmtree(tmp_dir)
    except Exception:
        try:
            shutil.rmtree(tmp_dir)
        except:
            pass
        pass
    if hepmc_named_weight_support:
        optional_dependences.append('--with-hepmc2hack')
        print "|| ------"
        print "|| Good, the following version of HEPMC\n||   %s\n|| was "%_HepTools['hepmc']['install_path']+\
                                                         "detected to support the writing of named weights."
        print "|| ------"        
    else:
        print r"|| /!\/!\/!\ "
        print "|| Note that he following version of HEPMC\n||   %s\n|| was "%_HepTools['hepmc']['install_path']+\
              "detected as *not* supporting named weights. The MG5aMC-PY8 interface will have to write "+\
              "a separate hepmc file\n|| for each extra weight potentially specified for studying systematic"+\
              " uncertainties (PDF, scale, merging, etc...)"
        print r"|| /!\/!\/!\ "
    
    # Jointhe optional dependencies detected
    optional_dependences = ' '.join(optional_dependences)

    # Now run the installation
    pythia_log = open(pjoin(_HepTools['pythia8']['install_path'],"pythia8_install.log"), "w")
    subprocess.call([pjoin(_installers_path,'installPYTHIA8.sh'),
                     _HepTools['pythia8']['install_path'],
                     _HepTools['pythia8']['tarball'][1],
                     _HepTools['hepmc']['install_path'],
                     _HepTools['zlib']['install_path'],
                     optional_dependences], 
                    stdout=pythia_log,
                    stderr=pythia_log)
    pythia_log.close()
#==================================================================================================
def finalize_installation(tool):
    """ Finalize the installation of the tool specified by copying all its libraries and executable
    files inside the corresponding lib and bin directories of HEPTools """
    
    # Create the necessary directories if they do not exist yet
    if not os.path.exists(pjoin(_installers_path,os.path.pardir,'bin')):
        os.mkdir(pjoin(_installers_path,os.path.pardir,'bin'))
    if not os.path.exists(pjoin(_installers_path,os.path.pardir,'include')):
        os.mkdir(pjoin(_installers_path,os.path.pardir,'include'))
    if not os.path.exists(pjoin(_installers_path,os.path.pardir,'lib')):
        os.mkdir(pjoin(_installers_path,os.path.pardir,'lib'))

    # List of all executables
    all_bin      = glob.glob(pjoin(_HepTools[tool]['install_path'],'bin','*'))
    all_include  = glob.glob(pjoin(_HepTools[tool]['install_path'],'include','*'))
    all_lib = glob.glob(pjoin(_HepTools[tool]['install_path'],'lib','*'))

    # Pick the special location of library for oneloop
    if tool=='oneloop':
        all_bin      = []
        all_include  = glob.glob(pjoin(_HepTools[tool]['install_path'],'*.mod'))
        all_lib      = [pjoin(_HepTools[tool]['install_path'],'libavh_olo.a')]
  
    # Pick special executable for mg5amc_py8_interface
    if tool=='mg5amc_py8_interface':
        all_bin      += [pjoin(_HepTools[tool]['install_path'],'MG5aMC_PY8_interface')]

    # Force static linking for Ninja
    if tool=='ninja':
        all_lib = [lib for lib in all_lib if not any(lib.endswith(ext) for ext in ['.so','.la','.dylib'])]

    for path in all_bin:
        if not os.path.exists(pjoin(_installers_path,os.path.pardir,'bin',os.path.basename(path))):
            os.symlink(os.path.relpath(path,pjoin(_installers_path,os.path.pardir,'bin')),
                               pjoin(_installers_path,os.path.pardir,'bin',os.path.basename(path)))
    for path in all_include:
        if not os.path.exists(pjoin(_installers_path,os.path.pardir,'include',os.path.basename(path))):
            os.symlink(os.path.relpath(path,pjoin(_installers_path,os.path.pardir,'include')),
                               pjoin(_installers_path,os.path.pardir,'include',os.path.basename(path)))
    for path in all_lib:
        if not os.path.exists(pjoin(_installers_path,os.path.pardir,'lib',os.path.basename(path))):
            os.symlink(os.path.relpath(path,pjoin(_installers_path,os.path.pardir,'lib')),
                               pjoin(_installers_path,os.path.pardir,'lib',os.path.basename(path)))

#==================================================================================================

def get_data(link):
    """ Pulls up a tarball from the web """
    if sys.platform == "darwin":
        program = ["curl","-OL"]
    else:
        program = ["wget"]
    print "Fetching data with command:\n  %s %s"%(' '.join(program),link)
    # Here shell=True is necessary. It is safe however since program and link are not
    
    subprocess.call(program+[link])
    return pjoin(os.getcwd(),os.path.basename(link))

# find a library in common paths 
def which_lib(lib):
    def is_lib(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.R_OK)

    if not lib:
        return None

    fpath, fname = os.path.split(lib)
    if fpath:
        if is_lib(lib):
            return lib
    else:
        locations = sum([os.environ[env_path].split(os.pathsep) for env_path in
           ["LIBRARY_PATH","PATH","DYLD_LIBRARY_PATH","LD_LIBRARY_PATH"] 
                                                  if env_path in os.environ],[])

        # Automatically look for the corresponding lib directories of the bin ones
        additional_locations = []
        for loc in locations:
            if os.path.basename(loc)=='bin':
                potential_other_lib_path = pjoin(os.path.dirname(loc),'lib')
                if os.path.isdir(potential_other_lib_path) and \
                   potential_other_lib_path not in locations:
                    additional_locations.append(potential_other_lib_path)
        locations.extend(additional_locations)

        # Add the default UNIX locations, but only after all the others have been searched for
        locations.extend([os.path.join(os.path.sep,'usr','lib'),os.path.join(os.path.sep,'usr','local','lib')])

        for path in locations:
            lib_file = os.path.join(path, lib)
            if is_lib(lib_file):
                # Check lhapdf version:
                if lib.lower().startswith('lhapdf'):
                    try:
                        proc = subprocess.Popen(
                          [pjoin(path,os.path.pardir,'bin','lhapdf-config'),'--version'], 
                          stdout=subprocess.PIPE)
                        if int(proc.stdout.read()[0])!=int(lib[-1:]):
                            raise
                    except:
                        continue
                return lib_file
    return None

# Find a dependency
def find_dependency(tool):
    """ Check if a tool is already installed or needs to be."""
    if _HepTools[tool]['install_path'] is None:
        return None
    elif _HepTools[tool]['install_path'].lower() != 'default':
        return _HepTools[tool]['install_path']
    else:
        # Make sure it hasn't been installed locally in the _prefix location already
        if any(os.path.exists(pjoin(_prefix,tool,'lib',lib)) for lib in 
                                           _HepTools[tool]['libraries']):
            return pjoin(_prefix,tool)
        # Treat the default case which is "install dependency if not found
        # otherwise use the one found".
        lib_found = None
        for lib in _HepTools[tool]['libraries']:
            lib_search = which_lib(lib)
            if not lib_search is None:
                lib_found = lib_search
                break
        if lib_found is None:
            return 'TO_INSTALL'
        else:
            # Return the root folder which is typically the install dir
            if os.path.dirname(lib_found).endswith('lib'):
                return os.path.abspath(pjoin(os.path.dirname(lib_found),'..'))
            else:
                return os.path.abspath(os.path.dirname(lib_found))

# Find lhapdf dependency
def find_lhapdf_dependency(tool):
    """ Decides which version of LHAPDF to use."""

    # First check the status for each version
    status_lhapdf5 = find_dependency('lhapdf5')
    status_lhapdf6 = find_dependency('lhapdf6')

    # Both have been vetoed
    if status_lhapdf5 is None and status_lhapdf6 is None:
        return None, None

    # If only one of the version is vetoed, install the remaining one:
    if status_lhapdf5 is None:
        return status_lhapdf6, 6
    if status_lhapdf6 is None:
        return status_lhapdf5, 5

    # At this stage the status can only take the values 'TO_INSTALL' or are alreayd installed
    # at a given path.
    # If both need to be installed, then chose LHAPDF 6
    if status_lhapdf5=='TO_INSTALL' and status_lhapdf6=='TO_INSTALL':
        return status_lhapdf6, 6

    # If both are already installed, then chose LHAPDF 6
    if status_lhapdf5 not in ['TO_INSTALL', None] and status_lhapdf6 not in ['TO_INSTALL', None]:
        return status_lhapdf6, 6

    # If only one is installed, then chose the already installed one.
    if status_lhapdf5 not in ['TO_INSTALL', None] and status_lhapdf6 in ['TO_INSTALL', None]:
        return status_lhapdf5, 5
    if status_lhapdf6 not in ['TO_INSTALL', None] and status_lhapdf5 in ['TO_INSTALL', None]:
        return status_lhapdf6, 6

    # All cases should be covered at this point
    print "Inconsistent LHPADF setup, the installer should have never reached this point."
    sys.exit(9)


def check_successful_installation(target):
    """ Check whether the installation of target was successful or not. """

    for f in _HepTools[target]['libraries']:
        if any(f.endswith(extension) for extension in _lib_extensions):
            if os.path.exists(pjoin(_HepTools[target]['install_path'],'lib',f)):
                return True
            if os.path.exists(pjoin(_HepTools[target]['install_path'],f)):
                return True
        if os.path.exists(pjoin(_HepTools[target]['install_path'],f)):
            return True
    return False

def install_with_dependencies(target,is_main_target=False):
    """ Recursive install function for a given tool, taking care of its dependencies"""
    
    # Make sure to actualize the path if set to default, as the target is now no longer a dependency but what
    # is being installed
    if _HepTools[target]['install_path'] == 'default':
        _HepTools[target]['install_path'] = pjoin(_prefix,target)

    for dependency in _HepTools[target]['mandatory_dependencies']+_HepTools[target]['optional_dependencies']:
        # Special treatment for lhapdf. 
        if dependency == 'lhapdf':
            path, version = find_lhapdf_dependency(dependency)
            if not version is None:
                try:
                    _HepTools[target]['mandatory_dependencies'][
                       _HepTools[target]['mandatory_dependencies'].index('lhapdf')]='lhapdf%d'%version
                except ValueError:
                    pass
                try:
                    _HepTools[target]['optional_dependencies'][
                       _HepTools[target]['optional_dependencies'].index('lhapdf')]='lhapdf%d'%version
                except ValueError:
                    pass
                dependency = 'lhapdf%d'%version
        # Special treatment of oneloop as well. We want it locally.
        elif dependency == 'oneloop':
            if os.path.isfile(pjoin(_prefix,'oneloop','libavh_olo.a')):
                path = pjoin(_prefix,'oneloop')
            else:
                path = 'TO_INSTALL'
        else:
            path = find_dependency(dependency)
        if path is None:
            if dependency in _HepTools[target]['optional_dependencies']:
                print "Optional '%s' dependency '%s' is disabled and will not be available."%(target, dependency)
                _HepTools[target]['optional_dependencies'].remove(dependency)
            else:
                print "Mandatory '%s' dependency '%s' unavailable. Exiting now."%(target, dependency)
                sys.exit(9)
        elif path=='TO_INSTALL':
            print "Detected '%s' missing dependency: '%s'. Will install it now."%(target, dependency)
            install_with_dependencies(dependency)
        else:
            print "'%s' dependency '%s' found at:\n  %s"%(target, dependency, path)
            _HepTools[dependency]['install_path']=path

    with TMP_directory() as tmp_path:
        # Get the source tarball if online
        if _HepTools[target]['tarball'][0]=='online':
            print "Downloading '%s' sources..."%target
            try:
                tarball_path = get_data(_HepTools[target]['tarball'][1])
            except Exception as e:
                print "Could not download data at '%s' because of:\n%s\n"%(_HepTools[target]['tarball'][1],str(e))
                sys.exit(9)
            _HepTools[target]['tarball'] = ('local',tarball_path)
        
        if not os.path.isdir(_HepTools[target]['install_path']):
            os.mkdir(_HepTools[target]['install_path'])
        print "Installing tool '%s'..."%target
        print "(you can follow the installation progress by running the command below in a separate terminal)\n  tail -f %s"%\
                                                     pjoin(_HepTools[target]['install_path'],'%s_install.log'%target)
        exec('install_%s(tmp_path)'%target)
        if not is_main_target:
            if check_successful_installation(target):
                # Successful installation, now copy the installed components directly under HEPTools
                finalize_installation(target)
                print "Successful installation of dependency '%s' in '%s'."%(target,_prefix)
                print "See installation log at '%s'."%pjoin(_HepTools[target]['install_path'],'%s_install.log'%target)
            else:
                print "A problem occured during the installation of dependency '%s'."%target
                try:
                    print "Content of the installation log file '%s':\n\n%s"%(\
                            pjoin(_HepTools[target]['install_path'],'%s_install.log'%target),
                            open(pjoin(_HepTools[target]['install_path'],'%s_install.log'%target),'r').read())
                except IOError:
                    print "No additional information on the installation problem available."
                print "Now aborting installation of tool '%s'."%target_tool
                sys.exit(9)

_environ = dict(os.environ)
try:   
    os.environ["CXX"]     = _cpp
    os.environ["FC"]      = _gfortran
    install_with_dependencies(target_tool,is_main_target=True)
except ZeroDivisionError as e:
    os.environ.clear()
    os.environ.update(_environ)
    print "The following error occured during the installation of '%s' (and its dependencies):\n%s"%(target_tool,repr(e))
    sys.exit(9)

os.environ.clear()
os.environ.update(_environ)

if check_successful_installation(target_tool):
    # Successful installation, now copy the installed components directly under HEPTools
    finalize_installation(target_tool)
    print "Successful installation of '%s' in '%s'."%(target_tool,_prefix)
    print "See installation log at '%s'."%pjoin(_HepTools[target_tool]['install_path'],'%s_install.log'%target_tool)
    sys.exit(0)
else:
    print "A problem occured during the installation of '%s'."%target_tool
    try:
      print "Content of the installation log file '%s':\n\n%s"%(\
        pjoin(_HepTools[target_tool]['install_path'],'%s_install.log'%target_tool),
        open(pjoin(_HepTools[target_tool]['install_path'],'%s_install.log'%target_tool),'r').read())
    except IOError:
      print "No additional information on the installation problem available."
    sys.exit(9)
