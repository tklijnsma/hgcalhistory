#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os, shutil, logging, uuid
import os.path as osp, numpy as np
from array import array
import hgcalhistory
logger = logging.getLogger('hgcalhistory')

import ROOT



class Histogram2D(object):

    def __init__(self):
        super(Histogram2D, self).__init__()
        self.x_bin_boundaries = None
        self.y_bin_boundaries = None
        self.data = None

    def set_x_bin_boundaries(self, bounds):
        self.x_bin_boundaries = bounds
        self.x_bin_centers = (bounds[:-1] + bounds[1:]) / 2.

    def set_y_bin_boundaries(self, bounds):
        self.y_bin_boundaries = bounds
        self.y_bin_centers = (bounds[:-1] + bounds[1:]) / 2.

    @property
    def n_bins_x(self):
        return len(self.x_bin_boundaries) - 1

    @property
    def n_bins_y(self):
        return len(self.y_bin_boundaries) - 1

    @property
    def n_bounds_x(self):
        return len(self.x_bin_boundaries)

    @property
    def n_bounds_y(self):
        return len(self.y_bin_boundaries)

    def find_nearest_bin_x(self, x):
        return (np.abs(self.x_bin_centers - x)).argmin()

    def find_nearest_bin_y(self, y):
        return (np.abs(self.y_bin_centers - y)).argmin()

    def _prepare_data(self):
        if self.data is None:
            self.data = np.zeros((self.n_bins_x, self.n_bins_y))

    def clear_data(self):
        self.data = None
        self._prepare_data()

    def to_TH2(self):
        TH2 = ROOT.TH2D(
            'TH2_{0}'.format(uuid.uuid4()), '',
            self.n_bins_x, array('d', self.x_bin_boundaries),
            self.n_bins_y, array('d', self.y_bin_boundaries),
            )
        ROOT.SetOwnership(TH2, False)
        for i_x in xrange(self.n_bins_x):
            for i_y in xrange(self.n_bins_y):
                TH2.SetBinContent(i_x+1, i_y+1, self.data[i_x][i_y])
        return TH2


class Histogram2DFillable(Histogram2D):

    def fill(self, x, y, value):
        self._prepare_data()
        i_x = self.find_nearest_bin_x(x)
        i_y = self.find_nearest_bin_y(y)
        self.data[i_x][i_y] += value

