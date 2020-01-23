#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os, shutil, logging
import os.path as osp
from array import array
import hgcalhistory
logger = logging.getLogger('hgcalhistory')

import ROOT


class Plot3D(object):
    """
    
    """
    canvas = hgcalhistory.rootutils.Canvas('auto', '', 0, 0, 1000, 618 )

    def __init__(self, name):
        super(Plot3D, self).__init__()
        self.name = name
        self.canvas.Clear()

    def draw_axes(self):
        self.view = ROOT.TView.CreateView(1)
        self.view.__class__ = ROOT.TView3D
        self.view.SetRange(
            -1., -1., -1,
            1., 1., 1.
            )

        self.axes = ROOT.TAxis3D()
        self.axes.Draw()

        self.axes.SetXTitle('x')
        self.axes.SetYTitle('y')
        self.axes.SetZTitle('z')
        self.axes.GetXaxis().CenterTitle()
        self.axes.GetYaxis().CenterTitle()
        self.axes.GetZaxis().CenterTitle()

        self.origin = ROOT.TPolyMarker3D(
            1,
            array('f', [0., 0., 0.]),
            9
            )
        self.origin.SetMarkerColor(ROOT.kRed)
        self.origin.Draw()

    def draw_helplines(self, xmin, ymin, zmin, xmax, ymax, zmax):
        self.helpline_xy_lower = ROOT.TPolyLine3D(
            3,
            array('f', [ xmin, xmax, xmax ]),
            array('f', [ ymax, ymax, ymin ]),
            array('f', [ zmin, zmin, zmin ]),
            )
        self.helpline_xy_lower.SetLineColor(ROOT.kGray)
        self.helpline_xy_lower.Draw()

        self.helpline_xy_upper = ROOT.TPolyLine3D(
            3,
            array('f', [ xmin, xmax, xmax ]),
            array('f', [ ymax, ymax, ymin ]),
            array('f', [ zmax, zmax, zmax ]),
            )
        self.helpline_xy_upper.SetLineColor(ROOT.kGray)
        self.helpline_xy_upper.Draw()

        self.helpline_z = ROOT.TPolyLine3D(
            2,
            array('f', [ xmax, xmax ]),
            array('f', [ ymax, ymax ]),
            array('f', [ zmin, zmax ]),
            )
        self.helpline_z.SetLineColor(ROOT.kGray)
        self.helpline_z.Draw()

    def save(self):
        self.canvas.save('plot3d_{0}.png'.format(self.name))
        self.canvas.save('plot3d_{0}.pdf'.format(self.name))

