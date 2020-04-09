#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os, shutil, logging, uuid, copy
import os.path as osp, numpy as np
from array import array
from math import pi
import hgcalhistory
logger = logging.getLogger('hgcalhistory')

import ROOT



def get_plot_base(
        x_min = 0, x_max = 1,
        y_min = 0, y_max = 1,
        x_title = 'x', y_title = 'y',
        set_title_sizes = True,
       ):
    base = ROOT.TH1F()
    ROOT.SetOwnership(base, False)
    base.SetName(str(uuid.uuid4()))
    base.GetXaxis().SetLimits(x_min, x_max)
    base.SetMinimum(y_min)
    base.SetMaximum(y_max)
    base.SetMarkerColor(0)
    base.GetXaxis().SetTitle(x_title)
    base.GetYaxis().SetTitle(y_title)
    if set_title_sizes:
        base.GetXaxis().SetTitleSize(0.06)
        base.GetYaxis().SetTitleSize(0.06)
    return base


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
            logger.info(
                'Opening new canvas %s for cls %s',
                cls.canvas.GetName(), cls.__name__
                )
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
        track_id = hit.geantTrackId()
        if track_id == 0:
            logger.warning('Hit %s has track id 0; Will give a pdgId of 1', hit)
            pdgid = 1
        else:
            pdgid = abs(event.get_track_by_id(track_id).pdgid())
        # logger.debug(
        #     'Hit %s is from track %s which has pdgid %s',
        #     hit.id(), hit.geantTrackId(), pdgid
        #     )
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


class HitMarkers(PlotBase):

    def __init__(self, name, do_coordinate='x', do_endcap='+'):
        super(HitMarkers, self).__init__(name)
        self.do_coordinate = do_coordinate
        self.do_endcap = do_endcap

    def divide_hits(self, event):
        graphs = {}
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
            z = hit.position_.z()
            coordinate = getattr(hit.position_, self.do_coordinate)()

            track_id = hit.track_id()
            if track_id == 0:
                pdgid = -1
            else:
                pdgid = abs(event.get_track_by_id(track_id).pdgid())

            if not pdgid in graphs:
                g = []
                graphs[pdgid] = g
            else:
                g = graphs[pdgid]
            # g.append((layer, coordinate))
            g.append((z, coordinate))
        return { key : np.array(g) for key, g in graphs.iteritems() }

    def draw_tracks(self, event):
        for track in event.tracks:
            track.get_projected_line(
                event.get_vertex_for_track(track),
                do_coordinate = self.do_coordinate
                ).Draw('SAME')

    def draw_layer_lines(self, layers=[5, 10, 15, 20]):
        for layer in layers:
            z = hgcalhistory.physutils.get_z_for_layer(layer, do_endcap=self.do_endcap)
            line = ROOT.TLine(z, self.y_min, z, self.y_max)
            ROOT.SetOwnership(line, False)
            line.SetLineColor(16)
            line.Draw()

    def legend(self):
        self.legend = ROOT.TLegend(0.19, 0.78, 0.39, 0.98)
        self.legend.SetBorderSize(0)
        self.legend.SetFillStyle(0)
        self.legend.SetNColumns(2)
        dummies = hgcalhistory.physutils.pdgid_legend_dummies()
        for dummy in dummies:
            dummy.Draw('LSAME')
            self.legend.AddEntry(dummy.GetName(), dummy.GetTitle(), 'l')
        self.legend.Draw()

    def plot(self, event):
        super(HitMarkers, self).plot()

        self.y_min = -250.
        self.y_max = 250.

        if self.do_endcap == '-':
            # self.x_min = -55.
            # self.x_max = 0.
            self.x_min = 1.1 * hgcalhistory.physutils.z_neg_layers[-1]
            self.x_max = hgcalhistory.physutils.z_neg_layers[0]
        else:
            # self.x_min = 0.
            # self.x_max = 55.
            self.x_min = hgcalhistory.physutils.z_pos_layers[0]
            self.x_max = 1.1 * hgcalhistory.physutils.z_pos_layers[-1]

        base = get_plot_base(
            x_min = self.x_min, x_max = self.x_max,
            y_min = self.y_min, y_max = self.y_max,
            x_title = 'z', y_title = self.do_coordinate
            )
        base.Draw('P')

        self.draw_layer_lines()

        self.canvas.SetLeftMargin(0.14)
        self.canvas.SetBottomMargin(0.14)
        self.canvas.SetTopMargin(0.02)
        self.canvas.SetRightMargin(0.02)

        graphs = self.divide_hits(event)
        for pdgid, graph in graphs.iteritems():
            n = len(graph)
            tgraph = ROOT.TGraph(
                n,
                array('f', graph[:,0]),
                array('f', graph[:,1]),
                )
            ROOT.SetOwnership(tgraph, False)
            tgraph.SetMarkerColor(hgcalhistory.physutils.pdgid_to_color(pdgid))
            tgraph.SetMarkerStyle(24)
            tgraph.Draw('PSAME')

        self.draw_tracks(event)
        self.legend()
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


class HitsPlotSplitMarkers(HitsPlotSplit):

    def __init__(self, name):
        super(HitsPlotSplitMarkers, self).__init__(name)

    def set_plots_to_positions(self):
        self.hitsplot_left_upper = hgcalhistory.plots.HitMarkers(self.name, 'x', '-')
        self.hitsplot_left_lower = hgcalhistory.plots.HitMarkers(self.name, 'y', '-')
        self.hitsplot_right_upper = hgcalhistory.plots.HitMarkers(self.name, 'x', '+')
        self.hitsplot_right_lower = hgcalhistory.plots.HitMarkers(self.name, 'y', '+')


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
        self.canvas.SetCanvasSize(1000, 718)
        self.draw_axes()
        # self.view.SetRange(*event.track_positions.minmax_xyz())
        # self.draw_helplines(*event.track_positions.minmax_xyz())
        self.minmax = (
            -250., # x min
            -250.0, # y min
            -550.0, # z min
            250.0, # x max
            250.0, # y max
            550.0, # z max
            )
        self.view.SetRange(*self.minmax)
        # self.draw_plane(hgcalhistory.physutils.z_pos_layers[0])
        # self.draw_plane(hgcalhistory.physutils.z_neg_layers[0])
        self.draw_helplines(*self.minmax)
        self.draw_vertices_and_tracks(event)

        # self.view.RotateView(45., 135.)
        # someint = ROOT.Int_t(0.)
        # self.view.SetView(10., 10., 10., someint)

        self.save()

    def draw_vertices_and_tracks(self, event):
        # event.vertex_positions.as_tpolymarker3d().Draw()
        for track in event.tracks:
            track.get_polyline(event.get_vertex_for_track(track)).Draw()

    def draw_plane(self, z):
        # plane = ROOT.TF2(
        #     str(uuid.uuid4()),
        #     '0*x + 0*y + {0}'.format(z),
        #     self.minmax[0], self.minmax[3],
        #     self.minmax[1], self.minmax[4]
        #     )
        # # plane.SetNpx(100)
        # # plane.SetNpy(100)
        # ROOT.SetOwnership(plane, False)
        # plane.Draw('lego2 same0 fb bb a')
        # plane.SetFillColorAlpha(ROOT.kRed, 0.5)
        # plane.SetLineColorAlpha(ROOT.kRed, 0.5)

        n_lines = 15
        xmin = self.minmax[0]
        xmax = self.minmax[3]
        ymin = self.minmax[1]
        ymax = self.minmax[4]
        dx = (xmax-xmin)/(n_lines-1)
        dy = (ymax-ymin)/(n_lines-1)

        x = xmin
        for i in range(n_lines):
            line = ROOT.TPolyLine3D(
                2,
                array('f', [ x, x ]),
                array('f', [ ymin, ymax ]),
                array('f', [ z, z ]),
                )
            line.SetLineColorAlpha(ROOT.kGray, 0.5)
            line.Draw()
            ROOT.SetOwnership(line, False)
            x += dx 

        y = ymin
        for i in range(n_lines):
            line = ROOT.TPolyLine3D(
                2,
                array('f', [ xmin, xmax ]),
                array('f', [ y, y ]),
                array('f', [ z, z ]),
                )
            line.SetLineColorAlpha(ROOT.kGray, 0.5)
            line.Draw()
            ROOT.SetOwnership(line, False)
            y += dy


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
            track_id = hit.track_id()
            if track_id == 0:
                hit.get_polymarker().Draw()
            else:
                hit.get_polymarker(track = event.get_track_by_id(hit.track_id())).Draw()
