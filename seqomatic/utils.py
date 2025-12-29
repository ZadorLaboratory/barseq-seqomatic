import logging
import os 
import pprint

from configparser import ConfigParser


####################################################
#
#                  common util functions
#  
####################################################

def create_folder_file(pos_path,name):
    if not os.path.exists(os.path.join(pos_path,name)):
        os.makedirs(os.path.join(pos_path,name))

def denoise(x):
    x[x<np.percentile(x, 85)]=0
    return x

def denoise(x):
    x[x<np.percentile(x, 85)]=0
    return x

def get_date():
    time_now = timezone('US/Pacific')
    date = str(datetime.now(time_now))[0:10]
    return date

def get_default_config():
    dc = os.path.expanduser('~/git/barseq-seqomatic/etc/seqomatic.conf')
    cp = ConfigParser()
    cp.read(dc)
    return cp

def get_file_name(path, kind):
    os.chdir(path)
    files = []
    for file in os.listdir():
        if file.endswith(kind):
            files.append(file)
    return files

def get_time():
    time_now = timezone('US/Pacific')
    time = str(datetime.now(time_now))[0:19] + "\n"
    return time


def hattop_convert(x):
    filterSize = (10, 10)
    kernel=cv2.getStructuringElement(cv2.MORPH_RECT, filterSize)
    return cv2.morphologyEx(x, cv2.MORPH_TOPHAT, kernel)



def hattop_convert(x):
    filterSize = (10, 10)
    kernel=cv2.getStructuringElement(cv2.MORPH_RECT, filterSize)
    return cv2.morphologyEx(x, cv2.MORPH_TOPHAT, kernel)



def ind2sub(array_shape, ind):
    # Gives repeated indices, replicates matlabs ind2sub
    cols = (ind.astype("int32") // array_shape[0])
    rows = (ind.astype("int32") % array_shape[0])
    return (rows, cols)



def sort_by(string):
    pos = np.array([int(s[s.find('Pos') + 3:s.find('.tif')]) for s in string])
    rearrange = np.argsort(pos)
    string = [string[i] for i in rearrange]
    return string

def clean_space(directory):
    for item in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, item)):
            shutil.rmtree(os.path.join(directory, item))


def get_resource_dir():
    '''
    Assume running from git for now. Go up two from script, and down to 'resource'

    '''
    script_file = os.path.abspath(__file__)
    (base, exe) = os.path.split(script_file)
    (libdir, script_dir) = os.path.split(base)
    rdir = os.path.join( libdir, 'resource'  )
    logging.debug(f'current script={script_file} libdir={libdir} resource_dir={rdir}')
    return rdir


def format_config(cp):
    '''
        Pretty print ConfigParser to standard string for logging.  
    '''
    cdict = {section: dict(cp[section]) for section in cp.sections()}
    s = pprint.pformat(cdict, indent=4)
    return s
