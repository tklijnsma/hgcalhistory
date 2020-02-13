#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path as osp
import logging, subprocess, os, shutil, re, pprint, csv
import hgcalhistory

logger = logging.getLogger('hgcalhistory')
DEFAULT_MGM = 'root://cmseos.fnal.gov'

_CLIENTCACHE = {}
def get_client(mgm):
    global _CLIENTCACHE
    mgm = mgm.strip('/')
    if not mgm in _CLIENTCACHE:
        logger.info('Starting new client for %s', mgm)
        from XRootD import client
        xrdclient = client.FileSystem(mgm)
        status, _ = xrdclient.ping()
        logger.info('Filesystem %s status: %s', mgm, status)
        if not status.ok:
            raise ValueError(
                'client {0} is not responsive: {1}'
                .format(mgm, status)
                )
        _CLIENTCACHE[mgm] = xrdclient
    else:
        xrdclient = _CLIENTCACHE[mgm]
    return xrdclient


def set_mgm(mgm):
    """
    Sets the default mgm
    """
    global DEFAULT_MGM
    DEFAULT_MGM = mgm
    logger.info('Default mgm set to %s', mgm)


def _unsafe_split_mgm(filename):
    """
    Takes a properly formatted path starting with 'root:' and containing '/store'
    """
    if not filename.startswith('root://'):
        raise ValueError(
            'Cannot split mgm; passed filename: {0}'
            .format(filename)
            )
    elif not '/store' in filename:
        raise ValueError(
            'No substring \'/store\' in filename {0}'
            .format(filename)
            )
    i = filename.index('/store')
    mgm = filename[:i]
    lfn = filename[i:]
    return mgm, lfn


def split_mgm(path, mgm=None):
    """
    Returns the mgm and lfn that the user most likely intended to
    if path starts with 'root://', the mgm is taken from the path
    if mgm is passed, it is used as is
    if mgm is passed AND the path starts with 'root://' AND the mgm's don't agree,
      an exception is thrown
    if mgm is None and path has no mgm, the default variable DEFAULT_MGM is taken
    """
    if path.startswith('root://'):
        _mgm, lfn = _unsafe_split_mgm(path)
        if not(mgm is None) and not _mgm == mgm:
            raise ValueError(
                'Conflicting mgms determined from path and passed argument: '
                'From path {0}: {1}, from argument: {2}'
                .format(path, _mgm, mgm)
                )
        mgm = _mgm
    elif mgm is None:
        mgm = DEFAULT_MGM
        lfn = path
    else:
        lfn = path
    # Some checks
    if not mgm.rstrip('/') == DEFAULT_MGM.rstrip('/'):
        logger.warning(
            'Using mgm {0}, which is not the default mgm {1}'
            .format(mgm, DEFAULT_MGM)
            )
    if not lfn.startswith('/store'):
        raise ValueError(
            'LFN {0} does not start with \'/store\'; something is wrong'
            .format(lfn)
            )
    return mgm, lfn


def _join_mgm_lfn(mgm, lfn):
    """
    Joins mgm and lfn, ensures correct formatting.
    Will throw an exception of the lfn does not start with '/store'
    """
    if not lfn.startswith('/store'):
        raise ValueError(
            'This function expects filenames that start with \'/store\''
            )
    if not mgm.endswith('/'): mgm += '/'
    return mgm + lfn


def format(src, mgm=None):
    """
    Formats a path to ensure it is a path on the SE
    """
    mgm, lfn = split_mgm(src, mgm=mgm)
    return _join_mgm_lfn(mgm, lfn)


# ___________________________________________________________
# Client operations

def create_directory(directory):
    """
    Creates a directory on the SE
    Does not check if directory already exists
    """
    import XRootD
    mgm, directory = split_mgm(directory)
    logger.warning('Creating directory on SE: {0}'.format(_join_mgm_lfn(mgm, directory)))
    client = get_client(mgm)
    status, _ = client.mkdir(directory, XRootD.client.flags.MkDirFlags.MAKEPATH)
    if not status.ok:
        raise ValueError(
            'Directory {0} on {1} could not be created: {2}'
            .format(directory, mgm, status)
            )
    logger.info('Created directory %s: %s', directory, status)



def get_statinfo(path):
    """
    """
    import XRootD
    mgm, path = split_mgm(path)
    client = get_client(mgm)
    
    status, statinfo = client.stat(path)
    if not status.ok:
        logger.info(
            'Trouble accessing {0}: {1}'
            .format(path, status)
            )
        return None
    return statinfo

def isdir(directory):
    statinfo = get_statinfo(directory)
    if statinfo is None:
        return False
    elif statinfo.flags == 19:
        return True
    else:
        return False

def isfile(directory):
    statinfo = get_statinfo(directory)
    if statinfo is None:
        return False
    elif statinfo.flags != 19:
        return True
    else:
        return False

def copy_to_se(src, dst, create_parent_directory=True):
    """
    Copies a file `src` to the storage element
    TODO: Use XRootD python bindings instead
    """
    mgm, dst = split_mgm(dst)
    dst = _join_mgm_lfn(mgm, dst)
    if create_parent_directory:
        parent_directory = osp.dirname(dst)
        create_directory(parent_directory)
    logger.warning('Copying {0} to {1}'.format(src, dst))
    cmd = [ 'xrdcp', '-s', src, dst ]
    hgcalhistory.utils.run_command(cmd)

def listdir(directory):
    mgm, directory = split_mgm(directory)
    client = get_client(mgm)
    status, listobj = client.dirlist(directory)
    if not status.ok:
        raise ValueError(
            'Could not list {0}: {1}'
            .format(directory, status)
            )
    return [ _join_mgm_lfn(mgm, osp.join(directory, item.name)) for item in listobj ]


def list_root_files(directory):
    """
    Lists all root files in a directory on the se
    """
    root_files = [ f for f in listdir(directory) if f.endswith('.root') ]
    root_files.sort() # Order should be the same every call
    return root_files

