#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, shutil, logging
import os.path as osp
import hgcalhistory
logger = logging.getLogger('hgcalhistory')

def _create_directory_no_checks(dirname, dry=False):
    """
    Creates a directory without doing any further checks.

    :param dirname: Name of the directory to be created
    :type dirname: str
    :param dry: Don't actually create the directory, only log
    :type dry: bool, optional
    """
    logger.warning('Creating directory {0}'.format(dirname))
    if not dry: os.makedirs(dirname)

def create_directory(dirname, force=False, must_not_exist=False, dry=False):
    """
    Creates a directory if certain conditions are met.

    :param dirname: Name of the directory to be created
    :type dirname: str
    :param force: Removes the directory `dirname` if it already exists
    :type force: bool, optional
    :param must_not_exist: Throw an OSError if the directory already exists
    :type must_not_exist: bool, optional
    :param dry: Don't actually create the directory, only log
    :type dry: bool, optional
    """
    if osp.isfile(dirname):
        raise OSError('{0} is a file'.format(dirname))
    isdir = osp.isdir(dirname)

    if isdir:
        if must_not_exist:
            raise OSError('{0} must not exist but exists'.format(dirname))
        elif force:
            logger.warning('Deleting directory {0}'.format(dirname))
            if not dry: shutil.rmtree(dirname)
        else:
            logger.warning('{0} already exists, not recreating')
            return
    _create_directory_no_checks(dirname, dry=dry)

class switchdir(object):
    """
    Context manager to temporarily change the working directory.

    :param newdir: Directory to change into
    :type newdir: str
    :param dry: Don't actually change directory if set to True
    :type dry: bool, optional
    """
    def __init__(self, newdir, dry=False):
        super(switchdir, self).__init__()
        self.newdir = newdir
        self._backdir = os.getcwd()
        self._no_need_to_change = (self.newdir == self._backdir)
        self.dry = dry

    def __enter__(self):
        if self._no_need_to_change:
            logger.info('Already in right directory, no need to change')
            return
        logger.info('chdir to {0}'.format(self.newdir))
        if not self.dry: os.chdir(self.newdir)

    def __exit__(self, type, value, traceback):
        if self._no_need_to_change:
            return
        logger.info('chdir back to {0}'.format(self._backdir))
        if not self.dry: os.chdir(self._backdir)


def is_string(string):
    # Python 2 / 3 compatibility (https://stackoverflow.com/a/22679982/9209944)
    try:
        basestring
    except NameError:
        basestring = str
    return isinstance(string, basestring)


def smart_list_root_files(rootfiles):
    """
    Takes a variable input `rootfiles`, and returns a formatted list of valid paths to
    root files.

    :param rootfiles: A string or list of paths to root files, or directories containing root files
    :type rootfiles: str, list
    """

    if is_string(rootfiles):
        rootfiles = [rootfiles]

    processed_root_files = []
    for rootfile in rootfiles:
        if rootfile.startswith('root:'):
            # This is on SE
            if hgcalhistory.seutils.isdir(rootfile):
                # It's a directory
                processed_root_files.extend(hgcalhistory.seutils.list_root_files(rootfile))
            elif hgcalhistory.seutils.isfile(rootfile):
                processed_root_files.append(hgcalhistory.seutils.format(rootfile))
            else:
                logger.error('Remote rootfile %s could not be found', rootfile)
        else:
            # This is local
            if osp.isdir(rootfile):
                processed_root_files.extend(
                    glob.glob(osp.join(rootfile, '*.root'))
                    )
            elif osp.isfile(rootfile):
                processed_root_files.append(rootfile)
            else:
                logger.error('Local rootfile %s could not be found', rootfile)

    if len(processed_root_files) == 0:
        logger.warning('No root files were found in %s', rootfiles)
    return processed_root_files
