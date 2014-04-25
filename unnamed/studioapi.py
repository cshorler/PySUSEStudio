#!/usr/bin/env python3
#
#  Python Wrapper for SUSE Studio REST API
#  Copyright (C) 2014  Christopher HORLER
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
"""
This module works with XML - internally it uses etree, if lxml.etree is
available, that is used - otherwise xml.etree.ElementTree is used.

Basic Usage:
$ python3

>>> import studioapi

>>> connection = studioapi.AuthConnection(username, password)
>>> studio = studioapi.StudioAPI(connection)

>>> studio.get_api_version()

"""
__all__ = ['AuthConnection', 'StudioAPI', 'StudioUtils']
__license__ = 'GPL-3, http://www.gnu.org/licenses/gpl.txt'
__author__ = "Chris Horler <cshorler@googlemail.com>"
__version__ = '2.0'

import sys

import urllib.request
from urllib.request import urlopen
from urllib.parse import urljoin, urlencode
from contextlib import closing

import os.path
import io
import email.generator
import email.policy
from email.mime.text import MIMEText
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.multipart import MIMEMultipart
import mimetypes

try:
    import lxml.etree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class HTTPPutRequest(urllib.request.Request):
    def __init__(self, *args, **kwargs):
        urllib.request.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return 'PUT'

class HTTPDeleteRequest(urllib.request.Request):
    def __init__(self, *args, **kwargs):
        urllib.request.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return 'DELETE'

class HTTPPostRequest(urllib.request.Request):
    def __init__(self, *args, **kwargs):
        urllib.request.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return 'POST'

class HTTPGetRequest(urllib.request.Request):
    def __init__(self, *args, **kwargs):
        urllib.request.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return 'GET'


class HTTPFormRequest(urllib.request.Request):
    def __init__(self, url, mime_msg, *args, **kwargs):
        if not isinstance(mime_msg, MIMEMultipart): raise TypeError
        
        mime_msg.policy = email.policy.HTTP
        mime_msg.set_boundary(email.generator._make_boundary())
        mime_msg._write_headers = lambda g: None

        buf = io.BytesIO()
        gen = email.generator.BytesGenerator(buf)
        gen.flatten(mime_msg)
        data = buf.getvalue()

        urllib.request.Request.__init__(self, url, data, *args, **kwargs)
        for h, v in mime_msg.items():
            self.add_unredirected_header(h, v) 

class HTTPPutFormRequest(HTTPFormRequest):
    def __init__(self, url, mime_msg, *args, **kwargs):
        HTTPFormRequest.__init__(self, url, mime_msg, *args, **kwargs)
    def get_method(self):
        return 'PUT'

class HTTPPostFormRequest(HTTPFormRequest):
    def __init__(self, url, mime_msg, *args, **kwargs):
        HTTPFormRequest.__init__(self, url, mime_msg, *args, **kwargs)
    def get_method(self):
        return 'POST'

class MIMEVar(MIMEText):
    def __init__(self, _name, _value, _subtype='plain', _charset=None, **kwargs):
        MIMEText.__init__(self, _value, _subtype, _charset)
        self.add_header('Content-Disposition', 'form-data', name=_name, **kwargs)

class MIMEFile(MIMENonMultipart):
    def __init__(self, name, file_path, **kwargs):
        contenttype = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        maintype, subtype = contenttype.split('/')
        filename = os.path.basename(file_path)
        #TODO: need to think about text encoding for text/*
        MIMENonMultipart.__init__(self, maintype, subtype)
        self.add_header('Content-Disposition', 'form-data', name=name, filename=filename)
        if maintype != 'text': self.add_header('Content-Type-Encoding', 'binary')
        with open(file_path, 'rb') as f:
            self.set_payload(f.read())



class BaseConnection:
    def __init__(self, host, api_path):
        self.addr = urljoin(host, api_path)
        self.opener = urllib.request.build_opener()
                
    def api_addr(self):
        return self.addr
        
    def api_opener(self):
        return self.opener


class AuthConnection(BaseConnection):
    """Wrapper for connection details and OpenerDirector
    """
    def __init__(self, username, password, host='https://susestudio.com', api_path='api/v2'):
        BaseConnection.__init__(self, host, api_path)

        auth_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        auth_manager.add_password(None, host, username, password)
        auth_handler = urllib.request.HTTPBasicAuthHandler(auth_manager)
        
        self.opener = urllib.request.build_opener(urllib.request.HTTPSHandler(debuglevel=1), auth_handler)


class StudioError(Exception):
    """Internal Library Error
    """
    def __init__(self, *args):
        Exception.__init__(self, *args)
        self.wrapped_exc = sys.exc_info()
        
        
class StudioAPI:
    """SUSE Studio REST API client implementation
    """
    def __init__(self, studio_connection):
        self.opener = studio_connection.api_opener()
        self.api_addr = studio_connection.api_addr()
        urllib.request.install_opener(self.opener)

    def _opener(self, request, raw=False):
        with urlopen(request) as response:
            try:
                if raw:
                    return response.read()
                else:
                    return ET.parse(response).getroot()
            except urllib.error.HTTPError as e:
                if e.code in [500,]: # TODO: list of HTTP Errors to wrap
                    raise StudioError("report error to the library maintainer")
                else:
                    raise
                
    ###############################################################
    # GENERAL INFORMATION
    ###############################################################
    def get_account(self):
        """GET /api/v1/user/account

        Returns information about the account, such as username, email address
        and disk quota.
        """
        req = HTTPGetRequest(self.api_addr+'/user/account')
        return self._opener(req)

    def get_api_version(self):
        """GET /api/v1/user/api_version

            Returns the running API version including the minor version.
        """
        req = HTTPGetRequest(self.api_addr+'/user/api_version')
        return self._opener(req)

    ############################################################
    # Template sets
    ##############################################################
    def get_template_sets(self, name=''):
        """GET /api/v1/user/template_sets
        GET /api/v1/user/template_sets/<name>
        
            List all template sets.
            List template set with name
            
            Template sets are used to group available templates by topic. The
            'default' template set contains all vanilla SUSE templates, 'mono'
            contains those that are optimized to be used for mono applications,
            for example.

            Arguments:

                name - Name of template
        """
        if name:
            url = self.api_addr + '/user/template_sets/%s' % name
        else:
            url = self.api_addr + '/user/template_sets'
        req = HTTPGetRequest(url)
        return self._opener(req)

    ############################################################
    # Appliances
    ###########################################################
    def get_appliances(self):
        """GET /api/v1/user/appliances

        List all appliances of the current user.
        """
        url = self.api_addr+'/user/appliances'
        req = HTTPGetRequest(url)
        return self._opener(req)

    def get_appliance_status(self, id):
        """GET /api/v1/user/appliances/<id>/status
            
        """
        url = self.api_addr+'/user/appliances/%s/status' % id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def create_appliance(self, clone_from, name='', arch=''):
        """POST /api/v1/user/appliances?clone_from=<appliance_id>&name=<name>
        &arch=<arch>

        Arguments:

            clone_from - The template the new appliance should be based on.
            name (optional) - The name of appliance
            arch (optional) - The architecture of the appliance
                              (x86_64 or i686)

        Create a new appliance by cloning a template or another appliance with
        the id appliance_id.

        If name is left out, a name will be generated. If arch is left out a
        i686 appliance will be created.
        """
        url = self.api_addr+'/user/appliances'
        data = urlencode({'clone_from':clone_from, 'name':name, 'arch':arch})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def delete_appliance(self, id):
        """DELETE /api/v1/user/appliances/<id>

        Arguments:

            id - Id of the appliance

        Delete appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s' % id
        req = HTTPDeleteRequest(url)
        return self._opener(req)

    ##################################################################
    # Repositories
    ##################################################################
    def get_appliance_repositories(self, id):
        """GET /api/v1/user/appliances/<id>/repositories

            Arguments:

                id - Id of the appliance

            List all repositories of the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/repositories' % id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def _set_appliance_repositories(self, appliance_id, xml_root=None):
        """PUT /api/v1/user/appliances/<appliance_id>/repositories

        THIS FUNCTION IS DESTRUCTIVE - it replaces the current repositories
        usually you want add_appliance_repository, or
        add_appliance_user_repository and not this function

            Arguments:

                appliance_id - id of the appliance
                xml_root - root node of repositories xml (ET.Element)
        """
        if isinstance(xml_root, ET.Element):
            xml_string = ET.tostring(xml_root)
        else:
            raise ValueError("expecting ET.Element (e.g. xml.etree.Element)")

        url = self.api_addr+'/user/appliances/%s/repositories' % appliance_id
        req = HTTPPutRequest(url=url, data=xml_string,
            headers={'Content-Type': 'application/xml'})
        return self._opener(req)

    def add_appliance_repository(self, appliance_id, repo_id):
        """POST /api/v1/user/appliances/<appliance_id>/cmd/add_repository?repo_id=<repo_id>

            Arguments:

                appliance_id - id of the appliance
                repo_id - id of the repository.

            Add the specified repository to the appliance with id appliance_id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/add_repository' % appliance_id
        data = urlencode({"repo_id":repo_id})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def remove_appliance_repository(self, id, repo_id):
        """POST /api/v1/user/appliances/<id>/cmd/remove_repository?repo_id=<repo_id>

            Arguments:

                id - Id of the appliance
                repo_id - Id of the repository.

            Remove the specified repository from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/remove_repository' % id
        data = urlencode({'repo_id':repo_id})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def add_appliance_user_repository(self, id):
        """POST /api/v1/user/appliances/<id>/cmd/add_user_repository

            Arguments:

                id - Id of the appliance

            Adds the according user repository (the one containing the uploaded
            RPMs) to the appliance.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/add_user_repository' % id
        req = HTTPPostRequest(url)
        return self._opener(req)

    ###########################################################################
    # Software
    ###########################################################################
    def get_appliance_software(self, id):
        """GET /api/v1/user/appliances/<id>/software

            Arguments:

                id - Id of the appliance

            List all selected packages and patterns of the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/software' % id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def set_appliance_software(self, appliance_id, xml_root=None):
        """PUT /api/v1/user/appliances/<appliance_id>/software

            Arguments:

                appliance_id - id of the appliance
                xml_root - root node of repositories xml (ET.Element)

            Update the list of selected packages and patterns of the appliance
            with id id.
        """
        if isinstance(xml_root, ET.Element):
            xml_string = ET.tostring(xml_root)
        else:
            raise ValueError("expecting ET.Element (e.g. xml.etree.Element)")

        url = self.api_addr+'/user/appliances/%s/software' % appliance_id
        req = HTTPPutRequest(url, data=xml_string,
            headers={'Content-Type': 'application/xml'})
        return self._opener(req)

    def get_appliance_installed_software(self, id, build_id=''):
        """GET /api/v1/user/appliances/<id>/software/installed?build_id=<build>

        Arguments:

            id - Id of the appliance
            build_id (optional) - Id of the build.

        List all packages and patterns that are installed. You can either
        specify the appliance with the appliance_id parameter, which will
        list the software that will installed with the next build or via an
        build id. That makes it possible to retrieve the installed software
        for older builds.
        """
        query = urlencode({'buildid':build_id})
        url = self.api_addr+'/user/appliances/%s/installed?%s' % (id, query)
        req = HTTPGetRequest(url)
        return self._opener(req)

    def add_appliance_software_package(self, id, name, version='', repository_id=''):
        """POST /api/v1/user/appliances/<id>/cmd/add_package?name=<name>
        &version=<version>&repository_id=<repo_id>

            Arguments:

                id - Id of the appliance
                name - Name of the package.
                version (optional) - Version of the package.
                repository_id (optional) - Repository to pick the package from.

            Add the specified package to the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/add_package' % id
        data = urlencode({'name':name, 'version':version,
            'repository_id':repository_id})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def remove_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/remove_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Remove the specified package from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/remove_package' % id
        data = urlencode({"name":name})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def add_appliance_software_pattern(self, id, name, version='', repository_id=''):
        """POST /api/v1/user/appliances/<id>/cmd/add_pattern?name=<name>
        &version=<version>&repository_id=<repo_id>

            Arguments:

                id - Id of the appliance
                name - Name of the pattern.
                version (optional) - Version of the pattern.
                repository_id (optional) - Repository to pick the pattern from.

            Add the specified pattern to the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/add_pattern' % id
        data = urlencode({'name':name, 'version':version, 'repository_id':repository_id})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def remove_appliance_software_pattern(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/remove_pattern?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the pattern.

            Remove the specified pattern from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/remove_pattern' % id
        data = urlencode({'name':name})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def ban_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/ban_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Ban a package from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/ban_package' % id
        data = urlencode({"name":name})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def unban_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/unban_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Unban a package from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/unban_package' % id
        data = urlencode({"name":name})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def search_appliance_software(self, id, q, all_fields=False, all_repos=False):
        """GET 
/api/v1/user/appliances/<id>/software/search?q=<search_string>&all_fields=<all_fields>&all_repos=<all_repos>

            Arguments:

                id - Id of the appliance
                q - The search string
                all_fields (optional) - Option to perform the search on all
                                        fields. Default is 'false'.
                all_repos (optional) - Option to perform the search on all
                                       repositories. Default is 'false'.

            Search all software that matches the given search_string. If the
            all_fields parameter is set to true all fields are considered,
            otherwise only the name of the package or pattern is matched against
            the search_string.  By default only software that is available to
            the appliance is considered, e.g. the search is limited to the
            repositories of this appliances. If you want to search in all
            repositories set the all_repos parameter to true.
        """
        query = urlencode({'q':q, 'all_fields':all_fields,
            'all_repos':all_repos})
        url = self.api_addr+'/user/appliances/%s/software/search?%s' % (id, query)
        req = HTTPGetRequest(url)
        return self._opener(req)

    #########################################################################
    # Image files
    #########################################################################
    def get_appliance_image_file(self, id, build_id, path):
        """GET /api/v1/user/appliances/<id>/image_files?build_id=<build_id>&path=<path_to_file>

            Arguments:

                id - Id of the appliance.
                build_id - Id of the build.
                path - Path to the file in the built appliance.

            Returns the file with the given path from an image.
        """
        query = urlencode({'build_id':build_id, 'path':path})
        url = self.api_addr+'/user/appliances/%s/image_files?%s' % (id, query)
        req = HTTPGetRequest(url)
        return self._opener(req)

    ############################################################################
    # GPG Keys
    ############################################################################
    def get_appliance_gpg_keys(self, id):
        """GET /api/v1/user/appliances/<id>/gpg_keys

            Arguments:

                id - Id of the appliance.

            Lists all GPG keys of the appliance with the id id.
        """
        url = self.api_addr+'/user/appliances/%s/gpg_keys' % id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def get_appliance_gpg_key(self, id, key_id):
        """GET /api/v1/user/appliances/<id>/gpg_keys/<key_id>

            Arguments:

                id - Id of the appliance.
                key_id - Id of the GPG key.

            Shows information on the GPG key with the id key_id.
        """
        url = self.api_addr+'/user/appliances/%s/gpg_keys/%s' % (id, key_id)
        req = HTTPGetRequest(url)
        return self._opener(req)

    def upload_appliance_gpg_key(self, id, name, target, key='', key_path=''):
        """POST /api/v1/user/appliances/<id>/gpg_keys?name=<name>&target=<target>&key=<the_key>

            Arguments:

                id - Id of the appliance.
                name - A name for the key.
                target - The target specifies in which keyring the key will be
                         imported. Possible values are: 'rpm'.
                key (optional) - The URL encoded key.

            Uploads a GPG key to the appliance with the id id. The key can
            either be given as the key parameter or wrapped as with form-based
            file uploads in HTML (RFC 1867) in the body of the POST request. The
            key will be imported into the keyring that is specified in the
            target parameter.
        """
        if key and key_file:
            raise ValueError("only use one of key or key_file, not both")
        elif not key and not key_file:
            raise ValueError("no key or key_file specified")
        
        url = self.api_addr+'/user/appliances/%s/gpg_keys' % id
        if key:
            data = urlencode({'name':name, 'target':target, 'key':key})
            req = HTTPPostRequest(url, data)
        else:
            msg = MIMEMultipart('form-data')
            msg.attach(MIMEVar('name', name))
            msg.attach(MIMEVar('target', target))
            msg.attach(MIMEFile('file', key_path))
            req = HTTPPostFormRequest(url, msg)
        return self._opener(req)

    def delete_appliance_gpg_key(self, id, key_id):
        """DELETE /api/v1/user/appliances/<id>/gpg_keys/<key_id>

            Arguments:

                id - Id of the appliance.
                key_id - Id of the GPG key.

            Deletes the GPG key with the id key_id from the appliance.
        """
        url = self.api_addr+'/user/appliances/%s/gpg_keys/%s' % (id, key_id)
        req = HTTPDeleteRequest(url)
        return self._opener(req)

    ########################################################################
    # Overlay files
    ########################################################################
    def get_appliance_overlay_files(self, id):
        """GET /api/v1/user/files?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all overlay files of appliance with id id.
        """
        url = self.api_addr+'/user/files?%s' % urlencode({'appliance_id':id})
        req = HTTPGetRequest(url)
        return self._opener(req)

    def upload_appliance_overlay_file(self, appliance_id, overlay_file=None,
        filename='', path='', owner='', group='', permissions='', enabled='',
        file_url=''):
        """POST /api/v1/user/files?appliance_id=<id>&filename=<name>&path=<path>
        &owner=<owner>&group=<group>&permissions=<perms>&enabled=<enabled>
        &url=<url>

            Arguments:

                appliance_id - Id of the appliance.

                mutually exclusive (one or the other, not both):
                overlay_file - file object to upload
                file_url - url of the file to add from the internet (HTTP and
                           FTP are supported)

                optional arguments:                                                                                  
                filename - The name of the file in the filesystem.
                path     - The path where the file will be stored.
                owner    - The owner of the file.
                group    - The group of the file.
                permissions - The permissions of the file.
                enabled  - Used to enable/disable this file for the builds.
        """
        if overlay_file and file_url:
            raise ValueError("use overlay_file or file_url, not both")
        
        data = {'appliance_id':id,
            'filename':filename,
            'path':path,
            'owner':owner,
            'group':group,
            'permissions':permissions,
            'enabled':enabled}

        if file_url:
            data['url'] = file_url
        elif overlay_file:
            data['file'] = overlay_file
        else:
            raise ValueError("file_url or overlay_file was invalid")

        url = self.api_addr+'/user/files'
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def get_overlay_file(self, file_id):
        """GET /api/v1/user/files/<file_id>/data

            Arguments:

                file_id - Id of the file.

            Returns the file with id file_id.
        """
        url = self.api_addr+'/user/files/%s/data' % file_id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def replace_overlay_file(self, file_id, local_path):
        """PUT /api/v1/user/files/<file_id>/data

            Arguments:

                file_id - Id of the file.

            Writes the content of the file with id file_id.
            The file is expected to be wrapped as with form-based file uploads
            in HTML (RFC 1867) in the body of the PUT request as the file
            parameter.
        """
        url = self.api_addr + 'user/files/%s/data' % file_id
        msg = MIMEMultipart('form-data')
        msg.attach(MIMEFile('file', local_path))
        req = HTTPPutFormRequest(url, msg)
        return self._opener(req)

    def get_overlay_file_metadata(self, id):
        """GET /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.

            Returns the meta data of the file with id file_id.
        """
        url = self.api_addr+'/user/files/%s' % id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def add_overlay_file_metadata(self, file_id, xml_root):
        """PUT /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.
                xml_root - root node of repositories xml (ET.Element)

            Writes the meta data of the file with id file_id.
        """
        if isinstance(xml_root, ET.Element):
            xml_string = ET.tostring(xml_root)
        else:
            raise ValueError("expecting ET.Element (e.g. xml.etree.Element)")

        data = {'file': urllib2.StringIO(xml_string)}
        url = self.api_addr+'/user/files/%s/data' % file_id
        req = HTTPPutRequest(url, data)
        return self._opener(req)

    def delete_overlay_file(self, id):
        """DELETE /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.

            Delete the file with id file_id and its meta data.
        """
        url = self.api_addr+'/user/files/%s' % id
        req = HTTPDeleteRequest(url)
        return self._opener(req)

    #####################################################################
    # Running builds
    #####################################################################
    def get_running_appliance_builds(self, appliance_id):
        """GET /api/v1/user/running_builds?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all running builds for the appliance with id id.
        """
        query = urlencode({'appliance_id':appliance_id})
        url = self.api_addr+'/user/running_builds?%s' % query
        req = HTTPGetRequest(url)
        return self._opener(req)

    def get_build_status(self, build_id):
        """GET /api/v1/user/running_builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Show status of the build with id build_id.
        """
        url = self.api_addr+'/user/running_builds/%s' % build_id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def add_build(self, appliance_id, force='', version='', image_type=''):
        """POST 
/api/v1/user/running_builds?appliance_id=<id>&force=<force>&version=<version>&image_type=<type>&multi=<multi>

            Arguments:

                appliance_id - Id of the appliance.
                force (optional) - Force a build even if it overwrites an
                                   already existing build.
                version (optional) - The version of the appliance.
                image_type (optional) - The format of the build. Supported are
                                        'xen','oem','vmx' and 'iso'.
                multi (optional) - If set to true it enables multibuild mode,
                                   which allows to build different formats of
                                   one version.

            Start a new build for the appliance with id id.
            If there already is a build with the same appliance settings (build
            type and version) an error is returned. In this case a build can be
            enforced by setting the optional force parameter to true. Optionally
            the appliance version and build type can be set with the version and
            image_type parameters.  It is possible to build different formats of
            one appliance version. Therefor do a first build and when it's done
            trigger the other formats with the multi parameter set to true.
        """
        url = self.api_addr+'/user/running_builds'
        data = urlencode({'appliance_id':id, 'force':force,
            'version':version, 'image_type':image_type})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def cancel_build(self, build_id):
        """DELETE /api/v1/user/running_builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Cancel build with id build_id.
        """
        url = self.api_addr+'/user/running_builds/%s' % build_id
        req = HTTPDeleteRequest(url)
        return self._opener(req)

    ###############################################################
    # Finished builds
    ###############################################################
    def get_completed_builds(self, appliance_id):
        """GET /api/v1/user/builds?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all completed builds for the appliance with id id.
        """
        url = self.api_addr+'/user/builds?%s' % urlencode({"appliance_id":id})
        req = HTTPGetRequest(url)
        return self._opener(req)

    def get_build_info(self, build_id):
        """GET /api/v1/user/builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Show build info of the build with id build_id.
        """
        url = self.api_addr+'/user/builds/%s' % build_id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def delete_build(self, build_id):
        """DELETE /api/v1/user/builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Delete build with id build_id.
        """
        url = self.api_addr+'/user/builds/%s' % build_id
        req = HTTPDeleteRequest(url)
        return self._opener(req)

    ##################################################################
    # RPM Uploads
    ##################################################################
    def get_base_system_rpms(self, base_system):
        """GET /api/v1/user/rpms?base_system=<base>

            Arguments:

                base_system - Base system of the RPM or archive, e.g. 11.1 or
                              SLED11.

            List all uploaded RPMs for the base system base.
        """
        query = urlencode({'base_system':base_system})
        url = self.api_addr+'/user/rpms?%s' % query
        req = HTTPGetRequest(url)
        return self._opener(req)

    def get_rpm_info(self, rpm_id):
        """GET /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Show information on the uploaded RPM with id rpm_id.
        """
        url = self.api_addr+'/user/rpms/%s' % rpm_id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def get_rpm(self, rpm_id):
        """GET /api/v1/user/rpms/<rpm_id>/data

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Returns the RPM with id rpm_id.
        """
        url = self.api_addr+'/user/rpms/%s/data' % rpm_id
        req = HTTPGetRequest(url)
        return self._opener(req)

    def upload_rpm(self, base_system, rpm_path):
        """POST /api/v1/user/rpms?base_system=<base>

            Arguments:

                base_system - Base system of the RPM or archive, e.g. 11.1 or
                              SLED11.

            Adds an RPM or archive to the user repository for appliances base on
            base.  The file is expected to be wrapped as with form-based file
            uploads in HTML (RFC 1867) in the body of the POST request as the
            file parameter.
        """
        url = self.api_addr+'/user/rpms'
        msg = MIMEMultipart('form-data')
        msg.attach(MIMEVar('base_system', base_system))
        msg.attach(MIMEFile('file', rpm_path))
        req = HTTPPostFormRequest(url, msg)
        return self._opener(req)

    def update_rpm(self, rpm_id, rpm_path):
        """PUT /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Update the content of the RPM or archive with the id rpm_id.
            The file is expected to be wrapped as with form-based file uploads
            in HTML (RFC 1867) in the body of the POST request as the file
            parameter.
        """
        url = self.api_addr+'/user/rpms/%s' % rpm_id
        msg = MIMEMultipart('form-data')
        msg.attach(MIMEFile('file', rpm_path))
        req = HTTPPutFormRequest(url, msg)
        return self._opener(req)

    def delete_rpm(self, rpm_id):
        """DELETE /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Deletes the RPM or archive with the id rpm_id from the user
            repository.
        """
        url = self.api_addr+'/user/rpms/%s' % rpm_id
        req = HTTPDeleteRequest(url)
        return self._opener(req)

    #################################################################
    # Repositories
    #################################################################
    def get_repositories(self, base_system=''): #, search_string=''):
        """GET /api/v1/user/repositories?base_system=<base>&filter=<search_string>

            Arguments:

                base_system (optional) - Limit the results to repositories with
                                         this base system.
                filter (optional) - Only show repositories matching this search
                                    string.

            Returns a list of repositories. If neither base_system nor filter
            are specified all available repositories are returned.
            When filtering the results with the filter parameter, the repository
            name, repository url and repository packages are searched.
        """
        criteria = []
        if base_system:
            criteria.append(('base_system', base_system))
        # FIXME: the search string / filter seems to cause all types of errors
        #if search_string:
        #    criteria.append(('filter', search_string))
        query = urlencode(criteria)
        url = self.api_addr+'/user/repositories?%s' % query
        req = HTTPGetRequest(url)
        return self._opener(req)

    def import_repository(self, repo_url, name):
        """POST /api/v1/user/repositories?url=<url>&name=<name>

            Arguments:

                url - Base url of the repository.
                name - Name for the repository.

            Imports a new repository into Studio. Returns the metadata for the
            created repository.
        """
        url = self.api_addr+'/user/repositories'
        data = urlencode({'url':repo_url, 'name':name})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    def get_repository_info(self, repo_id):
        """GET /api/v1/user/repositories/<id>

            Arguments:

                id - Id of the repository.

            Show information on the repository with the id id.
        """
        url = self.api_addr+'/user/repositories/%s' % repo_id
        req = HTTPGetRequest(url)
        return self._opener(req)

    ####################################################################
    # Testdrives
    ####################################################################
    def get_testdrives(self):
        """GET /api/v1/user/testdrives

            Returns a list of running testdrives.
        """
        url = self.api_addr + '/user/testdrives'
        req = HTTPGetRequest(url)
        return self._opener(req)

    def start_testdrive(self, build_id):
        """POST /api/v1/user/testdrives?build_id=<build_id>

            Arguments:

                build_id - Id of the build to run in testdrive.

            Starts a new testdrive session of the given build on the server and
            returns information about how to access it.

            Note: Testdrive sessions will be aborted when no client has
            connected after 60 seconds.
        """
        url = self.api_addr + '/user/testdrives'
        data = urlencode({'build_id':build_id})
        req = HTTPPostRequest(url, data)
        return self._opener(req)

    ####################################################################
    # Gallery
    ####################################################################
    def __gallery_search(self, keyword, username, page_number, results_per_page):
        if keyword:
            query = urlencode({'search': keyword, 'page': page_number, 'per_page': results_per_page})
        elif username:
            query = urlencode({'username': username, 'page': page_number, 'per_page': results_per_page})
        else:
            raise ValueError

        url = self.api_addr + '/user/gallery/appliances?%s' % query
        req = HTTPGetRequest(url)
        return self._opener(req)

    def gallery_latest_search(self, page_number=1, results_per_page=10):
        return self.__gallery_search('latest', None, page_number, results_per_page)

    def gallery_popular_search(self, page_number=1, results_per_page=10):
        return self.__gallery_search('popular', None, page_number, results_per_page)

    def gallery_keyword_search(self, keyword, page_number=1, results_per_page=10):
        return self.__gallery_search(keyword, None, page_number, results_per_page)

    def gallery_user_search(self, username, page_number=1, results_per_page=10):
        return self.__gallery_search(None, username, page_number, results_per_page)



class StudioUtils:
    @staticmethod
    def software_xml(appliance_id, packages=[], patterns=[]):
        """
        arguments:
            appliance_id - the appliance to update
            packages - a list of packages to add
            patterns - a list of patterns to add

        if packages need to be versioned, you need to amend the returned tree
        """
        root = ET.Element("software", type="array", appliance_id=appliance_id)
        for p in packages:
            ET.SubElement(root, "package").text = p
        for p in patterns:
            ET.SubElement(root, "patterns").text = p
        return root
            
    @staticmethod
    def rpm_xml(id, filename, size, archive, base_system, checksum):
        """
        arguments
            ***
        default to md5 checksum type - amend fragment if this is wrong!
        """
        tagdict = {'id':id, 'filename':filename, 'size':size, 'archive':archive,
            'base_system':base_system, 'checksum':checksum}
        tags = filter(lambda k: tagdict[k], tagdict)
        root = ET.Element("rpm")
        for tag in tags:
            ET.SubElement(root, tag).text = tagdict[tag]
        root.find("checksum").attrib['type'] = 'md5'
        return root

    @staticmethod
    def gallery_appliance_xml():
        """
        returns outline template - you HAVE to amend the return value!
        - you need to add valid accounts
        - you need to add valid configuration
        - you need to add formats

        **** this function does nothing except return a suitable empty xml
        to populate
        """
        root = ET.Element("gallery")
        appliance = ET.SubElement(root, "appliance")
        appliance_tags = ['id', 'name', 'version', 'release_notes', 'homepage',
            'description', 'publisher', 'username', 'based_on', 'formats',
            'configuration', 'keyboard_layout', 'language', 'timezone',
            'network', 'firewall', 'security']
        for tag in appliance_tags:
            ET.SubElement(appliance, tag)
        return root

