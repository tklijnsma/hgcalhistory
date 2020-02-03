#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os, shutil, logging, uuid, copy
import os.path as osp, numpy as np
from array import array
import hgcalhistory
logger = logging.getLogger('hgcalhistory')

import ROOT



class PlotBase(object):
    """docstring for PlotBase"""

    _has_canvas = False

    @classmethod
    def open_canvas(cls):
        """
        If there is no class canvas yet, open one up
        Try to share canvas per class instances at least, to avoid enormous
        memory leaks by ROOT
        """
        if not cls._has_canvas:
            cls.canvas = hgcalhistory.rootutils.Canvas('auto', '', 0, 0, 1000, 618 )
            cls._has_canvas = True

    def __init__(self, name):
        super(PlotBase, self).__init__()
        self.name = name
        self.plotname = type(self).__name__.replace('.','')
        self._is_subpad = False

    def set_pad(self, pad):
        self.canvas = pad
        self._has_canvas = True
        self._is_subpad = True

    def plot(self):
        self.__class__.open_canvas()
        self.canvas.Clear()

    def save(self):
        if not self._is_subpad:
            logger.debug('Saving {0}_{1}.png/pdf'.format(self.name, self.plotname))
            self.canvas.save('{0}_{1}.png'.format(self.name, self.plotname))
            self.canvas.save('{0}_{1}.pdf'.format(self.name, self.plotname))
        else:
            logger.debug('Not saving {0}_{1}.png/pdf (_is_subpad)'.format(self.name, self.plotname))
        

class HitsPlot(PlotBase):
    """
    """

    def __init__(self, name, do_coordinate='x', do_endcap='+'):
        super(HitsPlot, self).__init__(name)
        self.do_coordinate = do_coordinate
        self.do_endcap = do_endcap

        # Make 2D histograms that resemble the HGCAL geometry
        self.n_bins = 200
        self.n_bins_layers = 55

        # Bin boundaries of the x (or y) axis
        self.x_bounds = np.linspace(-250., 250., self.n_bins)
        # Bin boundaries of the z axis, i.e. the layers
        self.layer_bounds = np.linspace(0., self.n_bins_layers-1, self.n_bins_layers)
        if self.do_endcap == '-':
            self.layer_bounds = -self.layer_bounds[::-1]

        self.hist_x = hgcalhistory.datacontainers.Histogram2DFillable()
        self.hist_x.set_x_bin_boundaries(self.layer_bounds)
        self.hist_x.set_y_bin_boundaries(self.x_bounds)
        self.hist_x.clear_data()


    def plot(self, event):
        super(HitsPlot, self).plot()
        for hit in event.calohits:
            if not hit.inEE_:
                continue
            elif self.do_endcap == '+' and hit.position_.z() < 0.:
                continue
            elif self.do_endcap == '-' and hit.position_.z() > 0.:
                continue
            layer = hit.layer_
            if self.do_endcap == '-':
                layer = -layer
            self.hist_x.fill(layer, getattr(hit.position_, self.do_coordinate)(), hit.energy())

        self.plotname += '_' + self.do_coordinate + self.do_endcap
        self.canvas.cd()
        self.canvas.Clear()
        self.TH2 = self.hist_x.to_TH2()
        self.TH2.SetTitle('{0} vs. layers in {1}'.format(self.do_coordinate, self.do_endcap))
        self.TH2.Draw('COLZ')
        self.TH2.GetXaxis().SetTitle('Layers')
        self.TH2.GetYaxis().SetTitle(self.do_coordinate + ' [cm]')
        line = ROOT.TLine(0.0, 0.0, 1.0, 1.0)
        ROOT.SetOwnership(line, False)
        line.Draw()
        self.save()


class HitsPlotCoded(HitsPlot):
    """docstring for HitsPlotCoded"""
    def __init__(self, name, do_coordinate='x', do_endcap='+', color_coding='parent'):
        super(HitsPlotCoded, self).__init__(name, do_coordinate, do_endcap)
        assert color_coding in [ 'parent', 'pdgid' ]
        self.color_coding = color_coding
        self.hist_x_max = self.hist_x
        self.hist_x_index = copy.deepcopy(self.hist_x)
        self.hit_counter = 1

        self._geant_track_ids = {}
        self._pdgids = {}
        self._counter_ids = 1

    def get_integer_representing_parent(self, hit):
        """
        Returns a unique integer per parent track
        """
        geant_track_id = hit.geantTrackId()
        if not geant_track_id in self._geant_track_ids:
            self._geant_track_ids[geant_track_id] = self._counter_ids
            self._counter_ids += 1
        return self._geant_track_ids[geant_track_id]

    def get_integer_representing_pdgid(self, event, hit):
        """
        Returns a unique integer per pdgid
        """
        pdgid = abs(event.get_track_by_id(hit.geantTrackId()).pdgid())
        logger.debug(
            'Hit %s is from track %s which has pdgid %s',
            hit.id(), hit.geantTrackId(), pdgid
            )
        # if not pdgid in self._pdgids:
        #     self._pdgids[pdgid] = self._counter_ids
        #     self._counter_ids += 1
        # return self._pdgids[pdgid]
        return pdgid

    def get_hit_index_for_color_coding(self, event, hit):
        if self.color_coding == 'parent':
            return self.get_integer_representing_parent(hit)
        elif self.color_coding == 'pdgid':
            return self.get_integer_representing_pdgid(event, hit)

    def plot(self, event):
        super(HitsPlot, self).plot()
        for hit in event.calohits:
            if not hit.inEE_:
                continue
            elif self.do_endcap == '+' and hit.position_.z() < 0.:
                continue
            elif self.do_endcap == '-' and hit.position_.z() > 0.:
                continue
            layer = hit.layer_
            if self.do_endcap == '-':
                layer = -layer
            coordinate = getattr(hit.position_, self.do_coordinate)()
            energy = hit.energy()

            if energy > self.hist_x_max.get_value(layer, coordinate):
                self.hist_x_max.set_value(layer, coordinate, energy)
                self.hist_x_index.set_value(
                    layer,
                    coordinate,
                    self.get_hit_index_for_color_coding(event, hit)
                    )

        self.plotname += '_' + self.do_coordinate + self.do_endcap + '_' + self.color_coding
        self.canvas.cd()
        self.canvas.Clear()
        self.TH2 = self.hist_x_index.to_TH2()
        self.TH2.SetTitle(
            '{0} vs. layers in {1} by {2}'
            .format(self.do_coordinate, self.do_endcap, self.color_coding)
            )
        self.TH2.Draw('COLZ')
        self.TH2.GetXaxis().SetTitle('Layers')
        self.TH2.GetYaxis().SetTitle(self.do_coordinate + ' [cm]')
        line = ROOT.TLine(0.0, 0.0, 1.0, 1.0)
        ROOT.SetOwnership(line, False)
        line.Draw()
        self.save()




class HitsPlotSplit(PlotBase):
    """
    """

    def __init__(self, name):
        super(HitsPlotSplit, self).__init__(name)

    def make_pad(self, xmin, ymin, xmax, ymax):
        self.canvas.cd()
        pad = ROOT.TPad(
            'autopad-{0}'.format(uuid.uuid4()), '',
            xmin, ymin, xmax, ymax
            )
        ROOT.SetOwnership(pad, False)
        pad.SetRightMargin(0.20)
        pad.Draw()
        return pad

    def set_plots_to_positions(self):
        self.hitsplot_left_upper = hgcalhistory.plots.HitsPlot(self.name, 'x', '-')
        self.hitsplot_left_lower = hgcalhistory.plots.HitsPlot(self.name, 'y', '-')
        self.hitsplot_right_upper = hgcalhistory.plots.HitsPlot(self.name, 'x', '+')
        self.hitsplot_right_lower = hgcalhistory.plots.HitsPlot(self.name, 'y', '+')

    def plot(self, event):
        super(HitsPlotSplit, self).plot()
        self.canvas.SetCanvasSize(2*1000, 2*618)

        self.left_lower_pad = self.make_pad(0.0, 0.0, 0.5, 0.5)
        self.left_upper_pad = self.make_pad(0.0, 0.5, 0.5, 1.0)
        self.right_lower_pad = self.make_pad(0.5, 0.0, 1.0, 0.5)
        self.right_upper_pad = self.make_pad(0.5, 0.5, 1.0, 1.0)
        ROOT.gPad.Update()

        self.set_plots_to_positions()

        self.hitsplot_left_upper.set_pad(self.left_upper_pad)
        self.hitsplot_left_lower.set_pad(self.left_lower_pad)
        self.hitsplot_right_upper.set_pad(self.right_upper_pad)
        self.hitsplot_right_lower.set_pad(self.right_lower_pad)

        self.hitsplot_left_upper.plot(event)
        self.hitsplot_left_lower.plot(event)
        self.hitsplot_right_upper.plot(event)
        self.hitsplot_right_lower.plot(event)
        ROOT.gPad.Update()
        self.save()


class HitsPlotSplitColorCoded(HitsPlotSplit):

    def __init__(self, name, color_coding='parent'):
        super(HitsPlotSplit, self).__init__(name)
        self.color_coding = color_coding
        self.name += '_by' + self.color_coding

    def set_plots_to_positions(self):
        self.hitsplot_left_upper = hgcalhistory.plots.HitsPlotCoded(self.name, 'x', '-', self.color_coding)
        self.hitsplot_left_lower = hgcalhistory.plots.HitsPlotCoded(self.name, 'y', '-', self.color_coding)
        self.hitsplot_right_upper = hgcalhistory.plots.HitsPlotCoded(self.name, 'x', '+', self.color_coding)
        self.hitsplot_right_lower = hgcalhistory.plots.HitsPlotCoded(self.name, 'y', '+', self.color_coding)



class Plot3D(PlotBase):
    """
    
    """

    def plot(self, event):
        super(Plot3D, self).plot()
        self.draw_axes()
        self.view.SetRange(*event.track_positions.minmax_xyz())
        self.draw_helplines(*event.track_positions.minmax_xyz())
        self.draw_vertices_and_tracks(event)
        self.save()

    def draw_vertices_and_tracks(self, event):
        event.vertex_positions.as_tpolymarker3d().Draw()
        for track in event.tracks:
            track.get_polyline(event.get_vertex_for_track(track)).Draw()

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


class Plot3DWithCaloHits(Plot3D):
    def draw_vertices_and_tracks(self, event):
        """
        Like its parent but also draws the calohits
        """
        super(Plot3DWithCaloHits, self).draw_vertices_and_tracks(event)
        for hit in event.calohits:
            hit.get_polymarker(track = event.get_track_by_id(hit.track_id())).Draw()
