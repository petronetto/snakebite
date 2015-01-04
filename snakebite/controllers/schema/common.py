# -*- coding: utf-8 -*-

from __future__ import absolute_import
import colander
from snakebite.constants import TOKYO_GEOLOCATION


class Images(colander.SequenceSchema):
    image = colander.SchemaNode(colander.String(), validator=colander.url)


class Geolocation(colander.TupleSchema):
    longitude = colander.SchemaNode(colander.Float(), validator=colander.Range(-180, 180), missing=TOKYO_GEOLOCATION[0])
    latitude = colander.SchemaNode(colander.Float(), validator=colander.Range(-90, 90), missing=TOKYO_GEOLOCATION[1])