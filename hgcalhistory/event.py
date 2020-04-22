#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, shutil, logging
import os.path as osp, numpy as np, glob
from array import array
import hgcalhistory
logger = logging.getLogger('hgcalhistory')
import ROOT

import utils
from physutils import (
    hgcal_zmin_pos,
    hgcal_zmax_pos,
    hgcal_zmin_neg,
    hgcal_zmax_neg,
    )

class EventFactory(object):
    def __init__(self, *args, **kwargs):
        super(EventFactory, self).__init__()
        self.rootfiles = []
        for path in args:
            if path.endswith('.root'):
                self.rootfiles.append(path)
            elif path.startswith('root:'):
                import qondor
                qondor.subprocess_logger.setLevel(logging.ERROR)
                self.rootfiles.extend(qondor.seutils.ls_root(path))
            else:
                self.rootfiles.extend(glob.glob(osp.join(path, '*.root')))
        self.max_events = kwargs.get('max_events', None)
        self.tree = ROOT.TChain('Events')
        for rootfile in self.rootfiles:
            self.tree.Add(rootfile)
        # self.tree.__class__ = Event
        self.n_events = self.tree.GetEntries()
        logger.info(
            'Initialized factory with %s root files, %s events',
            len(self.rootfiles), self.n_events
            )

    def __iter__(self):
        for i_event in range(self.n_events):
            if i_event == self.max_events: raise StopIteration
            self.tree.GetEntry(i_event)
            yield Event(self.tree)

    def get(self, i):
        self.tree.GetEntry(i)
        return Event(self.tree)

    def __len__(self):
        return self.n_events if (self.max_events is None) else min(self.n_events, self.max_events)



class Event(object):
    def __init__(self, rootevent):
        super(Event, self).__init__()
        self.rootevent = rootevent
        
        self.tracks = []
        for t in self.rootevent.SimTracks_g4SimHits__SIM.product():
            t.__class__ = hgcalhistory.Track
            self.tracks.append(t)

        self.vertexs = []
        for v in self.rootevent.SimVertexs_g4SimHits__SIM.product():
            v.__class__ = hgcalhistory.Vertex
            self.vertexs.append(v)

        self.calohits = []
        for h in self.rootevent.PCaloHitWithPositions_PCaloHitWithPositionProducer__SIM.product():
            # Skip any non-HGCAL hits
            if not(h.inEE_ or h.inHsi_ or h.inHsc_):
                continue
            h.__class__ = hgcalhistory.CaloHitWithPosition
            self.calohits.append(h)

        self.n_tracks = len(self.tracks)
        self.n_vertexs = len(self.vertexs)

        self._tracks_position_collection = None
        self._vertexs_position_collection = None


    def has_photon(self):
        for track in self.tracks:
            if track.pdgid() == 22:
                return True
        else:
            return False

    def has_calohits_inEE(self):
        for hit in self.calohits:
            if hit.inEE_:
                return True
        else:
            return False

    def get_vertex_by_id(self, id):
        for v in self.vertexs:
            if v.id() == id:
                return v
        else:
            return None

    def get_track_by_id(self, id):
        for v in self.tracks:
            if v.id() == id:
                return v
        else:
            raise ValueError(
                'Track id {0}: no such track in event. Available track ids: {1}'
                .format(id, [v.id() for v in self.tracks])
                )

    def get_vertex_for_track(self, track):
        vertex_index = track.vertex_index()
        if vertex_index == -1:
            return None
        return self.vertexs[vertex_index]

    def _get_tracks_position_collection(self):
        if not(self._tracks_position_collection is None):
            return self._tracks_position_collection
        self._tracks_position_collection = PositionCollection()
        for t in self.tracks:
            self._tracks_position_collection.add(*t.xyz())
        return self._tracks_position_collection

    track_positions = property(_get_tracks_position_collection)

    def _get_vertexs_position_collection(self):
        if not(self._vertexs_position_collection is None):
            return self._vertexs_position_collection
        self._vertexs_position_collection = PositionCollection()
        for v in self.vertexs:
            self._vertexs_position_collection.add(*v.xyz())
        return self._vertexs_position_collection

    vertex_positions = property(_get_vertexs_position_collection)

    def debug_content_dump(self):
        for track in self.tracks:
            vertex = self.get_vertex_for_track(track)
            if vertex is None:
                logger.info('%s has no vertex', track)
                continue
            if vertex.track_id() != -1:
                track_for_vertex = self.get_track_by_id(vertex.track_id())
                if not track_for_vertex is None:
                    logger.debug(
                        '%s  <<  Vertex %s  <<  Track %s',
                        track, vertex, track_for_vertex.id()
                        )
                else:
                    logger.debug(
                        '%s  <<  Vertex %s  <<  Track %s (does not exist)',
                        track, vertex, vertex.track_id()
                        )
            else:
                logger.debug(
                    '%s  <<  Vertex %s (no parent track)',
                    track, vertex
                    )

        for hit in self.calohits:

            volume = 'Uns'
            if hit.inEE_:
                volume = 'EE '
            elif hit.inHsc_:
                volume = 'Hsc'
            elif hit.inHsi_:
                volume = 'Hsi'
            else:
                logger.warning('Hit %s has no HGCAL volume', hit.id())

            track_id = hit.track_id()
            if track_id == 0:
                logger.debug('Hit %s (%s) has track id 0 (no such track)', hit.id(), volume)
            else:
                try:
                    track = self.get_track_by_id(track_id)
                    logger.debug(
                        'Hit %s (%s) has track id %s which is pdgid %s',
                        hit.id(), volume, track_id, track.pdgid()
                        )
                except ValueError:
                    logger.debug(
                        'Hit %s (%s) has track id %s which does not exist',
                        hit.id(), volume, track_id
                        )

    def get_tracks_columnar(self, only_in_hgcal=True, filter_zero_tracks=True):
        """
        Returns the tracks in the event as columnar data
        Currently there are 8 columns. See the first lists in the code, below:        
        """
        track_x = []
        track_y = []
        track_z = []
        vertex_x = []
        vertex_y = []
        vertex_z = []
        pdgids = []
        track_ids = []
        vertex_ids = []

        for track in self.tracks:
            x_t, y_t, z_t = track.xyz()

            if filter_zero_tracks and x_t == 0. and y_t == 0. and z_t == 0.:
                logger.warning('Skipping %s ; points to origin', track)
                continue

            vertex = self.get_vertex_for_track(track)
            if vertex is None:
                logger.warning('Skipping track %s, no vertex associated', track)
                continue

            # logger.debug('%s --> %s', track, vertex)

            x_v, y_v, z_v = vertex.xyz()

            # Skip if not in hgcal
            if only_in_hgcal:
                if z_t > 0. and (
                    z_t < hgcal_zmin_pos and z_v < hgcal_zmin_pos
                    or z_t > hgcal_zmax_pos and z_v > hgcal_zmax_pos
                    ):
                    continue
                elif z_t < 0. and (
                    z_t < hgcal_zmin_neg and z_v < hgcal_zmin_neg
                    or z_t > hgcal_zmax_neg and z_v > hgcal_zmax_neg
                    ):
                    continue

            track_x.append(x_t)
            track_y.append(y_t)
            track_z.append(z_t)
            vertex_x.append(x_v)
            vertex_y.append(y_v)
            vertex_z.append(z_v)
            pdgids.append(track.pdgid())
            track_ids.append(track.id())
            vertex_ids.append(vertex.id())

        columns = np.stack(
            (
                np.array(track_x),
                np.array(track_y),
                np.array(track_z),
                np.array(vertex_x),
                np.array(vertex_y),
                np.array(vertex_z),
                np.array(pdgids),
                np.array(track_ids),
                np.array(vertex_ids)
                )
            ).T
        assert columns.shape == (len(track_x), 9)
        return columns

    def get_hits_columnar(self, only_in_hgcal=True):
        xs = []
        ys = []
        zs = []
        layers = []
        times = []
        energies = []
        track_ids = []
        which_detector = []
        pdgids = []
        for hit in self.calohits:
            x, y, z = hit.xyz()

            # Skip if not in hgcal
            if only_in_hgcal and not hgcalhistory.physutils.in_hgcal(z):
                continue

            xs.append(x)
            ys.append(y)
            zs.append(z)
            layers.append(hit.layer_)
            times.append(hit.time())
            energies.append(hit.energy())
            track_id = hit.geantTrackId()
            track_ids.append(track_id)

            if hit.inEE_:
                det = 1
            elif hit.inHsi_:
                det = 2
            elif hit.inHsc_:
                det = 3
            else:
                det = 0
            which_detector.append(det)

            # expensive loop
            for t in self.tracks:
                if t.id() == track_id:
                    pdgid = t.pdgid()
                    break
            else:
                pdgid = 0
            pdgids.append(pdgid)

        columns = np.stack(
            (
                np.array(xs),
                np.array(ys),
                np.array(zs),
                np.array(layers),
                np.array(times),
                np.array(energies),
                np.array(track_ids),
                np.array(which_detector),
                np.array(pdgids)
                )
            ).T
        assert columns.shape == (len(xs), 9)
        return columns


class PositionCollection(object):
    """docstring for PositionCollection"""
    def __init__(self):
        super(PositionCollection, self).__init__()
        self.x = []
        self.y = []
        self.z = []
        self.concat = []
    
    def add(self, x, y, z):
        self.x.append(x)
        self.y.append(y)
        self.z.append(z)
        self.concat.extend([x, y, z])

    def xmin(self):
        return min(self.x)
    def xmax(self):
        return max(self.x)
    def ymin(self):
        return min(self.y)
    def ymax(self):
        return max(self.y)
    def zmin(self):
        return min(self.z)
    def zmax(self):
        return max(self.z)

    def minmax_xyz(self):
        return self.xmin(), self.ymin(), self.zmin(), \
            self.xmax(), self.ymax(), self.zmax()

    def as_array(self):
        return array('f', self.concat)

    def as_tpolymarker3d(self, marker_style=9):
        r = ROOT.TPolyMarker3D(
            len(self.x),
            self.as_array(),
            marker_style
            )
        ROOT.SetOwnership(r, False)
        return r
