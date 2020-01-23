#  Towards Exposing the Truth for HGCAL

This repo contains some code to interpret the GEN-level .root-files outputted by a (e.g.) muon gun.

## Installation

```
cmsrel CMSSW_11_0_0_pre10
cd CMSSW_11_0_0_pre10/src
cmsenv
virtualenv hgcalenv
source hgcalenv/bin/activate
git clone https://github.com/tklijnsma/hgcalhistory.git
pip install -e hgcalhistory
```

## Example

```
from __future__ import print_function
import os.path as osp, logging
import hgcalhistory
logger = logging.getLogger('hgcalhistory')
import ROOT

def plot_rootfile(rootfile):
    for i_event, rootevent in enumerate(hgcalhistory.EventFactory(rootfile)):
        logger.info('Processing i_event %s in %s', i_event, rootfile)
        event = hgcalhistory.Event(rootevent)
        if len(event.tracks) == 0:
            logger.error('0 tracks found, skipping')
            continue
        elif len(event.vertexs) == 0:
            logger.error('0 vertices found, skipping')
            continue

        name = osp.basename(rootfile).replace('.root', '_{0}'.format(i_event))
        plot = hgcalhistory.Plot3D(name)
        plot.draw_axes()
        plot.view.SetRange(*event.track_positions.minmax_xyz())
        plot.draw_helplines(*event.track_positions.minmax_xyz())

        event.vertex_positions.as_tpolymarker3d().Draw()
        for track in event.tracks:
            track.get_polyline(event.get_vertex_for_track(track)).Draw()
        plot.save()

plot_rootfile('/path/to/GEN-level/rootfile.root')
```

## Example .root file from muon gun

Email me!
