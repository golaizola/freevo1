#!/usr/bin/env python

import sys
import os

try:
    import config

except ImportError:
    if 'FREEVO_HOME' in os.environ and os.environ['FREEVO_HOME']:
        os.chdir(os.environ['FREEVO_HOME'])
    else:
        os.chdir(os.path.join(os.path.dirname(sys.argv[0]), '..'))
    sys.path = [ 'src', ] + sys.path
    try:
        import config
    except:
        print 'can\'t find freevo files. Please set FREEVO_HOME to the Freevo root directory'
        sys.exit(1)


import util


def delete_old_files():
    print 'deleting old cache files from older freevo version'
    del_list = []
    for file in ('image-viewer-thumb.jpg', 'thumbnails/image-viewer-thumb.jpg'):
        file = os.path.join(config.FREEVO_CACHEDIR, file)
        if os.path.isfile(file):
            del_list.append(file)

    d = os.path.join(config.FREEVO_CACHEDIR, 'audio')
    if os.path.isdir(d):
        del_list.append(d)

    del_list += util.match_files(os.path.join(config.FREEVO_CACHEDIR, 'thumbnails'), ['jpg',])

    for f in del_list:
        if os.path.isdir(f):
            os.system('rm -rf %s' % f)
        else:
            os.system('rm %s' % f)


def cache_helper(result, dirname, names):
    result.append(dirname)
    return result

def cache_directories():
    import mmpython

    mmcache = '%s/mmpython' % config.FREEVO_CACHEDIR
    if not os.path.isdir(mmcache):
        os.mkdir(mmcache)
    mmpython.use_cache(mmcache)
    mmpython.mediainfo.DEBUG = 0
    mmpython.factory.DEBUG = 0
    
    all_dirs = []
    print 'caching directories...'
    for n, d in config.DIR_MOVIES + config.DIR_AUDIO + config.DIR_IMAGES:
        os.path.walk(d, cache_helper, all_dirs)
    for d in all_dirs:
        print d
        mmpython.cache_dir(d)
    
if __name__ == "__main__":
    delete_old_files()
    cache_directories()
    
