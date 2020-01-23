#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os.path as osp
import logging, os, uuid
from time import strftime

logger = logging.getLogger('root')

import ROOT
ROOT.gSystem.Load('libFWCoreFWLite')
ROOT.FWLiteEnabler.enable()
PLOTDIR = strftime('plots_hgcalhistory_%b%d')


class Canvas(ROOT.TCanvas):
    """docstring for Canvas"""

    def __init__(self, *arg, **kwarg):
        if arg[0] == 'auto':
            larg = list(arg)
            larg[0] = 'autocanvas-{0}'.format(uuid.uuid4())
            arg = tuple(larg)
        super(Canvas, self).__init__(*arg, **kwarg)

    def __del__(self):
        self.Close()

    def save(self, filename):
        save_canvas(self, filename)


def get_branches(treelike):
    """
    Returns a list of pairs, where each pair consists of first the name
    of the branch, and second a string indicating the type of class of the
    branch.
    """
    branch_names = []
    branches_array = treelike.GetListOfBranches()
    for i_var in range(branches_array.GetEntries()):
        branch = branches_array[i_var]
        branch_name = branch.GetName()
        if hasattr(branch, 'GetClassName'):
            class_name = branch.GetClassName()
            if len(class_name.strip()) == 0:
                class_name = branch.ClassName()
        elif hasattr(branch, 'ClassName'):
            class_name = branch.ClassName()
        else:
            class_name = 'UNKNOWN'
        logger.debug('Branch name: %s, class_name; %s', branch_name, class_name)
        branch_names.append((branch_name, class_name))
    return branch_names


class quick_canvas(object):
    """
    Temporarily open a canvas, for quick plots
    """
    def __init__(self, width=1000, height=800, canvas_name='auto'):
        super(canvas, self).__init__()
        if canvas_name == 'auto':
            canvas_name = 'autocanvas-{0}'.format(uuid.uuid4())
        self.canvas_name = canvas_name
        self.width = width
        self.height = height
        
    def __enter__(self):
        logger.debug('Opening new canvas (%sx%s) %s', self.width, self.height, self.canvas_name)
        # self.canvas = ROOT.TCanvas(self.canvas_name, self.canvas_name, self.width, self.height)
        self.canvas = Canvas(self.canvas_name, self.canvas_name, self.width, self.height)
        return self.canvas

    def __exit__(self, type, value, traceback):
        self.canvas.Close()


def create_plotdir():
    if not osp.isdir(PLOTDIR):
        logger.debug('Creating %s', PLOTDIR)
        os.makedirs(PLOTDIR)


def save_canvas(canvas, filename):
    create_plotdir()
    out = osp.join(PLOTDIR, filename)
    logger.debug('Saving %s', out)
    canvas.SaveAs(out)


