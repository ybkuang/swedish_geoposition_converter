#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Project: Plankton Toolbox. http://plankton-toolbox.org
# Author: Arnold Andreasson, info@mellifica.se
# Copyright (c) 2010-2012 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License as follows:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
This module contains an implementation of the "Gauss Conformal Projection 
(Transverse Mercator), Krügers Formulas" and a set of parameters for the most 
commonly used map projections in Sweden. The Gauss-Krüger formula transforms 
between geodetic coordinates and grid coordinates.

Standard transformations are implemented as pure functions. For transformations 
to and from local projections the SwedishGeoPositionConverter class must be
used. Note that WGS 84 is used when naming some of the standard transformation 
functions. A more correct name is SWEREF 99 (without TM or ddmm), but WGS 84 is 
one of many modern reference systems and well known by GPS users.
 
Supported map projections are:
- RT 90: rt90_5.0_gon_v, rt90_2.5_gon_v, rt90_0.0_gon_v, rt90_2.5_gon_o, 
  rt90_5.0_gon_o.
- RT90 Bessel 1841: bessel_rt90_7.5_gon_v, bessel_rt90_5.0_gon_v, 
  bessel_rt90_2.5_gon_v, bessel_rt90_0.0_gon_v, bessel_rt90_2.5_gon_o, 
  bessel_rt90_5.0_gon_o. 
- SWEREF99: sweref_99_tm, sweref_99_1200, sweref_99_1330, sweref_99_1500, 
  sweref_99_1630, sweref_99_1800, sweref_99_1415, sweref_99_1545, 
  sweref_99_1715, sweref_99_1845, sweref_99_2015, sweref_99_2145, 
  sweref_99_2315. 

Used formula and parameters can be found here (in Swedish): 
http://www.lantmateriet.se/geodesi/
"""

import math

# Globals used to reuse converter objects.
rt90_converter = None
sweref99tm_converter = None

def rt90_to_sweref99tm(x, y):
    """ Converts from RT 90 2.5 gon V to SWEREF 99 TM. """
    global rt90_converter
    global sweref99tm_converter
    if (rt90_converter == None):
        rt90_converter = SwedishGeoPositionConverter("rt90_2.5_gon_v")
    if (sweref99tm_converter == None):
        sweref99tm_converter = SwedishGeoPositionConverter("sweref_99_tm")
    lat, long = rt90_converter.gridToGeodetic(x, y)
    return sweref99tm_converter.geodeticToGrid(lat, long)
    
def sweref99tm_to_rt90(n, e):
    """ Converts from SWEREF 99 TM to RT 90 2.5 gon V. """
    global rt90_converter
    global sweref99tm_converter
    if (rt90_converter == None):
        rt90_converter = SwedishGeoPositionConverter("rt90_2.5_gon_v")
    if (sweref99tm_converter == None):
        sweref99tm_converter = SwedishGeoPositionConverter("sweref_99_tm")
    lat, long = sweref99tm_converter.gridToGeodetic(n, e)
    return rt90_converter.geodeticToGrid(lat, long)
    
def wgs84_to_rt90(lat, long):
    """ Converts from WGS 84 to RT 90 2.5 gon V. """
    global rt90_converter
    if (rt90_converter == None):
        rt90_converter = SwedishGeoPositionConverter("rt90_2.5_gon_v")
    return rt90_converter.geodeticToGrid(lat, long)
    
def rt90_to_wgs84(x, y):
    """ Converts from RT 90 2.5 gon V to WGS 84. """
    global rt90_converter
    if (rt90_converter == None):
        rt90_converter = SwedishGeoPositionConverter("rt90_2.5_gon_v")
    return rt90_converter.gridToGeodetic(x, y)
    
def wgs84_to_sweref99tm(lat, long):
    """ Converts from WGS 84 to SWEREF 99 TM. """
    global sweref99tm_converter
    if (sweref99tm_converter == None):
        sweref99tm_converter = SwedishGeoPositionConverter("sweref_99_tm")
    return sweref99tm_converter.geodeticToGrid(lat, long)
    
def sweref99tm_to_wgs84(n, e):
    """ Converts from SWEREF 99 TM to WGS 84. """
    global sweref99tm_converter
    if (sweref99tm_converter == None):
        sweref99tm_converter = SwedishGeoPositionConverter("sweref_99_tm")
    return sweref99tm_converter.gridToGeodetic(n, e)

class SwedishGeoPositionConverter(object):
    """
    Implementation of the Gauss-Kr�ger formula for transformations between 
    geodetic and grid coordinates. Contains parameters for the most commonly
    used map projections in Sweden. These projections are based on the 
    Bessel 1841, GRS 80 and the SWEREF 99 ellipsoids.   
    """
    def __init__(self, projection = "sweref_99_tm"):
        """ """        
        # Local variables.
        self._initialized = False
        self._axis = 0.0 # Semi-major axis of the ellipsoid.
        self._flattening = 0.0 # Flattening of the ellipsoid.
        self._central_meridian = 0.0 # Central meridian for the projection.
        self._lat_of_origin = 0.0 # Latitude of origin (not used).
        self._scale = 0.0 # Scale on central meridian.
        self._false_northing = 0.0 # Offset for origo.
        self._false_easting = 0.0 # Offset for origo.
        self._a_roof = 0.0
        self._A = 0.0
        self._B = 0.0
        self._C = 0.0
        self._D = 0.0
        self._beta1 = 0.0
        self._beta2 = 0.0
        self._beta3 = 0.0
        self._beta4 = 0.0
        self._delta1 = 0.0
        self._delta2 = 0.0
        self._delta3 = 0.0
        self._delta4 = 0.0
        self._Astar = 0.0
        self._Bstar = 0.0
        self._Cstar = 0.0
        self._Dstar = 0.0
        # Initial calculations.
        self._setProjection(projection)
        self._prepareEllipsoid()
    
    def geodeticToGrid(self, latitude, longitude):
        """
        Transformation from geodetic coordinates to grid coordinates.
        @param latitude
        @param longitude
        @return (north, east)
        (North corresponds to X in RT 90 and N in SWEREF 99.) 
        (East corresponds to Y in RT 90 and E in SWEREF 99.)
        """
        if (self._initialized == False):
            return None
        deg_to_rad = math.pi / 180.0
        phi = latitude * deg_to_rad
        lambda_long = longitude * deg_to_rad
        lambda_zero = self._central_meridian * deg_to_rad
        
        phi_star = phi - math.sin(phi) * math.cos(phi) * (self._A + \
                self._B*math.pow(math.sin(phi), 2) + \
                self._C*math.pow(math.sin(phi), 4) + \
                self._D*math.pow(math.sin(phi), 6))
        delta_lambda = lambda_long - lambda_zero
        xi_prim = math.atan(math.tan(phi_star) / math.cos(delta_lambda))
        eta_prim = math.atanh(math.cos(phi_star) * math.sin(delta_lambda))
        north = self._scale * self._a_roof * (xi_prim + \
                self._beta1 * math.sin(2.0*xi_prim) * math.cosh(2.0*eta_prim) + \
                self._beta2 * math.sin(4.0*xi_prim) * math.cosh(4.0*eta_prim) + \
                self._beta3 * math.sin(6.0*xi_prim) * math.cosh(6.0*eta_prim) + \
                self._beta4 * math.sin(8.0*xi_prim) * math.cosh(8.0*eta_prim)) + \
                self._false_northing
        east = self._scale * self._a_roof * (eta_prim + \
                self._beta1 * math.cos(2.0*xi_prim) * math.sinh(2.0*eta_prim) + \
                self._beta2 * math.cos(4.0*xi_prim) * math.sinh(4.0*eta_prim) + \
                self._beta3 * math.cos(6.0*xi_prim) * math.sinh(6.0*eta_prim) + \
                self._beta4 * math.cos(8.0*xi_prim) * math.sinh(8.0*eta_prim)) + \
                self._false_easting
#        north = round(north * 1000.0) / 1000.0
#        east = round(east * 1000.0) / 1000.0
        return (north, east)
    
    def gridToGeodetic(self, north, east):
        """
        Transformation from grid coordinates to geodetic coordinates.
        @param north (corresponds to X in RT 90 and N in SWEREF 99.)
        @param east (corresponds to Y in RT 90 and E in SWEREF 99.)
        @return (latitude, longitude)
        """
        if (self._initialized == False):
            return None

        deg_to_rad = math.pi / 180
        lambda_zero = self._central_meridian * deg_to_rad
        xi = (north - self._false_northing) / (self._scale * self._a_roof)        
        eta = (east - self._false_easting) / (self._scale * self._a_roof)
        xi_prim = xi - \
                self._delta1*math.sin(2.0*xi) * math.cosh(2.0*eta) - \
                self._delta2*math.sin(4.0*xi) * math.cosh(4.0*eta) - \
                self._delta3*math.sin(6.0*xi) * math.cosh(6.0*eta) - \
                self._delta4*math.sin(8.0*xi) * math.cosh(8.0*eta)
        eta_prim = eta - \
                self._delta1*math.cos(2.0*xi) * math.sinh(2.0*eta) - \
                self._delta2*math.cos(4.0*xi) * math.sinh(4.0*eta) - \
                self._delta3*math.cos(6.0*xi) * math.sinh(6.0*eta) - \
                self._delta4*math.cos(8.0*xi) * math.sinh(8.0*eta)
        phi_star = math.asin(math.sin(xi_prim) / math.cosh(eta_prim))
        delta_lambda = math.atan(math.sinh(eta_prim) / math.cos(xi_prim))
        lon_radian = lambda_zero + delta_lambda
        lat_radian = phi_star + math.sin(phi_star) * math.cos(phi_star) * \
                (self._Astar + \
                 self._Bstar*math.pow(math.sin(phi_star), 2) + \
                 self._Cstar*math.pow(math.sin(phi_star), 4) + \
                 self._Dstar*math.pow(math.sin(phi_star), 6))      
        lat = lat_radian * 180.0 / math.pi
        lon = lon_radian * 180.0 / math.pi
        return (lat, lon)
    
    def _prepareEllipsoid(self):
        """ Prepare calculations only related to the choosen ellipsoid. """
        if (self._initialized == False):
            return None
        
        e2 = self._flattening * (2.0 - self._flattening)
        n = self._flattening / (2.0 - self._flattening)
        self._a_roof = self._axis / (1.0 + n) * (1.0 + n*n/4.0 + n*n*n*n/64.0)
        # Prepare ellipsoid-based stuff for geodetic_to_grid.
        self._A = e2
        self._B = (5.0*e2*e2 - e2*e2*e2) / 6.0
        self._C = (104.0*e2*e2*e2 - 45.0*e2*e2*e2*e2) / 120.0
        self._D = (1237.0*e2*e2*e2*e2) / 1260.0
        self._beta1 = n/2.0 - 2.0*n*n/3.0 + 5.0*n*n*n/16.0 + 41.0*n*n*n*n/180.0
        self._beta2 = 13.0*n*n/48.0 - 3.0*n*n*n/5.0 + 557.0*n*n*n*n/1440.0
        self._beta3 = 61.0*n*n*n/240.0 - 103.0*n*n*n*n/140.0
        self._beta4 = 49561.0*n*n*n*n/161280.0
        # Prepare ellipsoid-based stuff for grid_to_geodetic.
        self._delta1 = n/2.0 - 2.0*n*n/3.0 + 37.0*n*n*n/96.0 - n*n*n*n/360.0
        self._delta2 = n*n/48.0 + n*n*n/15.0 - 437.0*n*n*n*n/1440.0
        self._delta3 = 17.0*n*n*n/480.0 - 37*n*n*n*n/840.0
        self._delta4 = 4397.0*n*n*n*n/161280.0
        self._Astar = e2 + e2*e2 + e2*e2*e2 + e2*e2*e2*e2
        self._Bstar = -(7.0*e2*e2 + 17.0*e2*e2*e2 + 30.0*e2*e2*e2*e2) / 6.0
        self._Cstar = (224.0*e2*e2*e2 + 889.0*e2*e2*e2*e2) / 120.0
        self._Dstar = -(4279.0*e2*e2*e2*e2) / 1260.0

    def _setProjection(self, projection):
        """
        Parameters for RT90 and SWEREF99TM.
        Parameters for RT90 are choosen to eliminate the differences between 
        Bessel and GRS80-ellipsoids.
        Note: Bessel-variants should only be used if lat/long are given as
        RT90-lat/long based on the old Bessel 1841 ellipsoid.
        Parameter: projection (string). Must match if-statement.
        """
        # RT90 parameters, GRS 80 ellipsoid.
        if (projection == "rt90_7.5_gon_v"):
            self._grs80()
            self._central_meridian = 11.0 + 18.375/60.0
            self._scale = 1.000006000000
            self._false_northing = -667.282
            self._false_easting = 1500025.141
            self._initialized = True
        elif (projection == "rt90_5.0_gon_v"):
            self._grs80()
            self._central_meridian = 13.0 + 33.376/60.0
            self._scale = 1.000005800000
            self._false_northing = -667.130
            self._false_easting = 1500044.695
            self._initialized = True
        elif (projection == "rt90_2.5_gon_v"):
            self._grs80()
            self._central_meridian = 15.0 + 48.0/60.0 + 22.624306/3600.0
            self._scale = 1.00000561024
            self._false_northing = -667.711
            self._false_easting = 1500064.274
            self._initialized = True
        elif (projection == "rt90_0.0_gon_v"):
            self._grs80()
            self._central_meridian = 18.0 + 3.378/60.0
            self._scale = 1.000005400000
            self._false_northing = -668.844
            self._false_easting = 1500083.521
            self._initialized = True
        elif (projection == "rt90_2.5_gon_o"):
            self._grs80()
            self._central_meridian = 20.0 + 18.379/60.0
            self._scale = 1.000005200000
            self._false_northing = -670.706
            self._false_easting = 1500102.765
            self._initialized = True
        elif (projection == "rt90_5.0_gon_o"):
            self._grs80()
            self._central_meridian = 22.0 + 33.380/60.0
            self._scale = 1.000004900000
            self._false_northing = -672.557
            self._false_easting = 1500121.846
            self._initialized = True
        # RT90 parameters, Bessel 1841 ellipsoid.
        elif (projection == "bessel_rt90_7.5_gon_v"):
            self._bessel()
            self._central_meridian = 11.0 + 18.0/60.0 + 29.8/3600.0
            self._initialized = True
        elif (projection == "bessel_rt90_5.0_gon_v"):
            self._bessel()
            self._central_meridian = 13.0 + 33.0/60.0 + 29.8/3600.0
            self._initialized = True
        elif (projection == "bessel_rt90_2.5_gon_v"):
            self._bessel()
            self._central_meridian = 15.0 + 48.0/60.0 + 29.8/3600.0
            self._initialized = True
        elif (projection == "bessel_rt90_0.0_gon_v"):
            self._bessel()
            self._central_meridian = 18.0 + 3.0/60.0 + 29.8/3600.0
            self._initialized = True
        elif (projection == "bessel_rt90_2.5_gon_o"):
            self._bessel()
            self._central_meridian = 20.0 + 18.0/60.0 + 29.8/3600.0
            self._initialized = True
        elif (projection == "bessel_rt90_5.0_gon_o"):
            self._bessel()
            self._central_meridian = 22.0 + 33.0/60.0 + 29.8/3600.0
            self._initialized = True
        # SWEREF99TM and SWEREF99ddmm  parameters.
        elif (projection == "sweref_99_tm"):
            self._sweref99()
            self._central_meridian = 15.00
            self._lat_of_origin = 0.0
            self._scale = 0.9996
            self._false_northing = 0.0
            self._false_easting = 500000.0
            self._initialized = True
        elif (projection == "sweref_99_1200"):
            self._sweref99()
            self._central_meridian = 12.00
            self._initialized = True
        elif (projection == "sweref_99_1330"):
            self._sweref99()
            self._central_meridian = 13.50
            self._initialized = True
        elif (projection == "sweref_99_1500"):
            self._sweref99()
            self._central_meridian = 15.00
            self._initialized = True
        elif (projection == "sweref_99_1630"):
            self._sweref99()
            self._central_meridian = 16.50
            self._initialized = True
        elif (projection == "sweref_99_1800"):
            self._sweref99()
            self._central_meridian = 18.00
            self._initialized = True
        elif (projection == "sweref_99_1415"):
            self._sweref99()
            self._central_meridian = 14.25
            self._initialized = True
        elif (projection == "sweref_99_1545"):
            self._sweref99()
            self._central_meridian = 15.75
            self._initialized = True
        elif (projection == "sweref_99_1715"):
            self._sweref99()
            self._central_meridian = 17.25
            self._initialized = True
        elif (projection == "sweref_99_1845"):
            self._sweref99()
            self._central_meridian = 18.75
            self._initialized = True
        elif (projection == "sweref_99_2015"):
            self._sweref99()
            self._central_meridian = 20.25
            self._initialized = True
        elif (projection == "sweref_99_2145"):
            self._sweref99()
            self._central_meridian = 21.75
            self._initialized = True
        elif (projection == "sweref_99_2315"):
            self._sweref99()
            self._central_meridian = 23.25
            self._initialized = True
        # For testing.
        elif (projection == "test_case"):
            # Test-case:
            #    Lat: 66 0'0", long: 24 0'0".
            #    X:1135809.413803 Y:555304.016555.
            self._axis = 6378137.0
            self._flattening = 1.0 / 298.257222101
            self._central_meridian = 13.0 + 35.0/60.0 + 7.692000/3600.0
            self._lat_of_origin = 0.0
            self._scale = 1.000002540000
            self._false_northing = -6226307.8640
            self._false_easting = 84182.8790
            self._initialized = True
        else:
            self._initialized = False
    
    def _grs80(self):
        """ Default parameters for the GRS80 ellipsoid. """
        self._axis = 6378137.0
        self._flattening = 1.0 / 298.257222101
        self._lat_of_origin = 0.0

    def _bessel(self):
        """ Default parameters for the Bessel 1841 ellipsoid. """
        self._axis = 6377397.155
        self._flattening = 1.0 / 299.1528128
        self._lat_of_origin = 0.0
        self._scale = 1.0
        self._false_northing = 0.0
        self._false_easting = 1500000.0

    def _sweref99(self):
        """ Default parameters for the SWEREF 99 ellipsoid. """
        self._axis = 6378137.0
        self._flattening = 1.0 / 298.257222101
        self._lat_of_origin = 0.0
        self._scale = 1.0
        self._false_northing = 0.0
        self._false_easting = 150000.0
