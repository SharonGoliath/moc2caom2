# -*- coding: utf-8 -*-
# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2020.                            (c) 2020.
#  Government of Canada                 Gouvernement du Canada
#  National Research Council            Conseil national de recherches
#  Ottawa, Canada, K1A 0R6              Ottawa, Canada, K1A 0R6
#  All rights reserved                  Tous droits réservés
#
#  NRC disclaims any warranties,        Le CNRC dénie toute garantie
#  expressed, implied, or               énoncée, implicite ou légale,
#  statutory, of any kind with          de quelque nature que ce
#  respect to the software,             soit, concernant le logiciel,
#  including without limitation         y compris sans restriction
#  any warranty of merchantability      toute garantie de valeur
#  or fitness for a particular          marchande ou de pertinence
#  purpose. NRC shall not be            pour un usage particulier.
#  liable in any event for any          Le CNRC ne pourra en aucun cas
#  damages, whether direct or           être tenu responsable de tout
#  indirect, special or general,        dommage, direct ou indirect,
#  consequential or incidental,         particulier ou général,
#  arising from the use of the          accessoire ou fortuit, résultant
#  software.  Neither the name          de l'utilisation du logiciel. Ni
#  of the National Research             le nom du Conseil National de
#  Council of Canada nor the            Recherches du Canada ni les noms
#  names of its contributors may        de ses  participants ne peuvent
#  be used to endorse or promote        être utilisés pour approuver ou
#  products derived from this           promouvoir les produits dérivés
#  software without specific prior      de ce logiciel sans autorisation
#  written permission.                  préalable et particulière
#                                       par écrit.
#
#  This file is part of the             Ce fichier fait partie du projet
#  OpenCADC project.                    OpenCADC.
#
#  OpenCADC is free software:           OpenCADC est un logiciel libre ;
#  you can redistribute it and/or       vous pouvez le redistribuer ou le
#  modify it under the terms of         modifier suivant les termes de
#  the GNU Affero General Public        la “GNU Affero General Public
#  License as published by the          License” telle que publiée
#  Free Software Foundation,            par la Free Software Foundation
#  either version 3 of the              : soit la version 3 de cette
#  License, or (at your option)         licence, soit (à votre gré)
#  any later version.                   toute version ultérieure.
#
#  OpenCADC is distributed in the       OpenCADC est distribué
#  hope that it will be useful,         dans l’espoir qu’il vous
#  but WITHOUT ANY WARRANTY;            sera utile, mais SANS AUCUNE
#  without even the implied             GARANTIE : sans même la garantie
#  warranty of MERCHANTABILITY          implicite de COMMERCIALISABILITÉ
#  or FITNESS FOR A PARTICULAR          ni d’ADÉQUATION À UN OBJECTIF
#  PURPOSE.  See the GNU Affero         PARTICULIER. Consultez la Licence
#  General Public License for           Générale Publique GNU Affero
#  more details.                        pour plus de détails.
#
#  You should have received             Vous devriez avoir reçu une
#  a copy of the GNU Affero             copie de la Licence Générale
#  General Public License along         Publique GNU Affero avec
#  with OpenCADC.  If not, see          OpenCADC ; si ce n’est
#  <http://www.gnu.org/licenses/>.      pas le cas, consultez :
#                                       <http://www.gnu.org/licenses/>.
#
#  $Revision: 4 $
#
# ***********************************************************************
#

import logging
import os

from astropy.io import fits
from astropy.time import Time
from mocpy import STMOC, MOC
from caom2 import Observation, ReleaseType, ProductType
from caom2pipe import manage_composable as mc
import vos


def visit(observation, **kwargs):
    mc.check_param(observation, Observation)
    working_directory = kwargs.get('working_directory', './')
    science_file = kwargs.get('science_file')
    cadc_client = kwargs.get('cadc_client')

    if science_file is None:
        raise mc.CadcException('science_file must be defined.')
    science_fqn = f'{working_directory}/{science_file}'
    science_out_fqn = science_fqn.replace('.fits', '_moc.fits').replace(
        '.fz', '')

    cert_fqn = f'/usr/src/app/cadcproxy.pem'
    vos_client = None
    # this check is just how to know if TaskType == SCRAPE
    if cadc_client is not None:
        vos_client = vos.Client(vospace_certfile=cert_fqn)
    vos_space = 'vos:goliaths/moc'
    dest_moc_fqn = f'{vos_space}/' \
                   f'{science_file.replace(".fits", "_moc.fits" ).replace(".fz", "")}'
    dest_stmoc_fqn = f'{vos_space}/' \
                     f'{science_file.replace(".fits", "_stmoc.fits" ).replace(".fz", "")}'

    count = 0
    for plane in observation.planes.values():
        if not plane.product_id.endswith('p'):
            continue
        e_params = ''
        if plane.energy is not None:
            e_min = f'{plane.energy.bounds.lower:E}'
            e_max = f'{plane.energy.bounds.upper:E}'
            e_name = plane.energy.bandpass_name
            e_params = f'addprop=E_MIN={e_min} addprop=E_MAX={e_max} ' \
                  f'addprop=E_NAME={e_name}'
        t_params = ''
        t_min = None
        if plane.time is not None:
            t_min = plane.time.bounds.lower
            t_max = plane.time.bounds.upper
            t_params = f'addprop=T_MIN={t_min} addprop=T_MAX={t_max}'

        moc_cmd = f'/usr/lib/jvm/java-11-openjdk-amd64/bin/java -jar ' \
                  f'/usr/lib/Aladin4Daniel.jar -mocgen order=16 ' \
                  f'in={science_fqn} out={science_out_fqn} hdu=all ' \
                  f'{e_params} {t_params}'
        mc.exec_cmd(moc_cmd)

        with fits.open(science_out_fqn, mode='update') as hdus:
            logging.info(f'Updating {science_out_fqn} to pass fitsverify.')
            cur_date = hdus[1].header.get('DATE')
            iso_date = mc.make_time(cur_date)
            hdus[1].header['DATE'] = iso_date.isoformat()
            hdus.flush()
            count += _vos_write(science_out_fqn, dest_moc_fqn, vos_client)
            temp = None
            if dest_moc_fqn in plane.artifacts:
                temp = plane.artifacts[dest_moc_fqn]
            plane.artifacts[dest_moc_fqn] = mc.get_artifact_metadata(
                science_out_fqn, ProductType.SCIENCE, ReleaseType.DATA,
                dest_moc_fqn, temp)

        if t_min is not None:
            stmoc_out_fqn = science_fqn.replace(
                '.fits', '_stmoc.fits').replace('.fz', '')
            logging.info(f'Creating a Time MOC in {stmoc_out_fqn}')
            if os.path.exists(stmoc_out_fqn):
                os.unlink(stmoc_out_fqn)
            moc = MOC.from_fits(science_out_fqn)
            times_start = Time([t_min], format='mjd', scale='tdb')
            times_end = Time([t_max], format='mjd', scale='tdb')
            stmoc = STMOC.from_spatial_coverages(times_start, times_end, [moc])
            stmoc.write(stmoc_out_fqn)
            count += _vos_write(stmoc_out_fqn, dest_stmoc_fqn, vos_client)

            temp = None
            if dest_stmoc_fqn in plane.artifacts:
                temp = plane.artifacts[dest_stmoc_fqn]
            plane.artifacts[dest_stmoc_fqn] = mc.get_artifact_metadata(
                stmoc_out_fqn, ProductType.SCIENCE, ReleaseType.DATA,
                dest_stmoc_fqn, temp)

        return {'artifacts': count}


# get a todo list from reading a vospace directory
# do the work of the todo list

# questions to think about:
#
# - what to do about configurable information - e.g. vos:sfabbro/megawcs
# that won't ever be re-used?
# - what to do about a data source like vos, where I don't want to
# write, for example, a retrieval method?
# should I write a client in execute_composable where the retrieval method
# is provided from the data source class?
# seems somewhat reasonable
# could handle the ftpclient that way too?


def _vos_write(source_fqn, dest_fqn, vos_client):
    count = 0
    try:
        if vos_client is not None:
            vos_client.copy(source_fqn, dest_fqn, send_md5=True)
            count = 1
    except Exception as e:
        import traceback
        logging.debug(traceback.format_exc())
        logging.error(f'Encountered {e} when writing to {dest_fqn}')
    return count
