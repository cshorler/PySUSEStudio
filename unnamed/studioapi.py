#!/usr/bin/env python

"""
TODO: Example usage

import studioapi

connection = studioapi.AuthConnection(username, password)
studio = studioapi.StudioAPI(connection)

studio.get_api_version()

"""
__all__ = ['AuthConnection', 'StudioAPI', 'StudioUtils']
__license__ = 'GPL v.2 http://www.gnu.org/licenses/gpl.txt'
__author__ = "Chris Horler <cshorler@googlemail.com>"
__version__ = '1.0-pre1'

import urllib
import urllib2
import urlparse


class HTTPPutRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return 'PUT'


class HTTPDeleteRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return 'DELETE'


class HTTPPostRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return 'POST'


class HTTPGetRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)
    def get_method(self):
        return 'GET'


class BaseConnection:
    def __init__(self, host, api_path):
        self.addr = urlparse.urljoin(host, api_path)
        self.opener = urllib2.build_opener()
                
    def api_addr(self):
        return self.addr
        
    def api_opener(self):
        return self.opener


class AuthConnection(BaseConnection):
    """Wrapper for connection details and OpenerDirector
    """
    def __init__(self, username, password, host='http://susestudio.com',
        api_path='api/v1'):
        BaseConnection.__init__(self, host, api_path)

        auth_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        auth_manager.add_password(None, host, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(auth_manager)
        
        self.opener = urllib2.build_opener(
             urllib2.HTTPHandler(debuglevel=1), auth_handler)


class StudioAPI:
    """SUSE Studio REST API client implementation
    """
    def __init__(self, studio_connection):
        self.opener = studio_connection.api_opener()
        self.opener.add_handler(MultipartPostHandler())
        self.api_addr = studio_connection.api_addr()
        urllib2.install_opener(self.opener)

    ###############################################################
    # GENERAL INFORMATION
    ################################################################
    def get_api_key(self):
        """GET /user/show_api_key

            Returns an HTML page which contains the API key flagged as:

            <span class="studio:api_key">ksdjfu93r</span>
        """
        url_parts = urlparse.urlsplit(self.api_addr)
        url = urlparse.urlunsplit(url_parts._replace(path='/user/show_api_key'))
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def get_account(self):
        """GET /api/v1/user/account

             Returns information about the account, such as username, email address and disk quota.
        """
        req = HTTPGetRequest(self.api_addr+'/user/account')
        return urllib2.urlopen(req)

    def get_api_version(self):
        """GET /api/v1/user/api_version

            Returns the running API version including the minor version.
        """
        req = HTTPGetRequest(self.api_addr+'/user/api_version')
        return urllib2.urlopen(req)

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
        query = urllib.urlencode({'name':name})
        req = HTTPGetRequest(self.api_addr + '/user/template_sets/?%s' % query)
        return urllib2.urlopen(req)

    ############################################################
    # Appliances
    ###########################################################
    def get_appliances(self):
        """GET /api/v1/user/appliances

            List all appliances of the current user.
        """
        url = self.api_addr+'/user/appliances'
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def get_appliance_status(self, id):
        """GET /api/v1/user/appliances/<id>/status
            
        """
        url = self.api_addr+'/user/appliances/%s/status' % id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def create_appliance(self, clone_from, name='', arch=''):
        """POST /api/v1/user/appliances?clone_from=<appliance_id>&name=<name>&arch=<arch>

            Arguments:

                clone_from - The template the new appliance should be based on.
                name (optional) - The name of appliance
                arch (optional) - The architecture of the appliance
                                  (x86_64 or i686)

            Create a new appliance by cloning a template or another appliance
            with the id appliance_id.

            If name is left out, a name will be generated. If arch is left out a
            i686 appliance will be created.
        """
        url = self.api_addr+'/user/appliances'
        data = urllib.urlencode({'clone_from':clone_from, 'name':name,
                                 'arch':arch})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def delete_appliance(self, id):
        """DELETE /api/v1/user/appliances/<id>

            Arguments:

                id - Id of the appliance

            Delete appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s' % id
        req = HTTPDeleteRequest(url)
        return urllib2.urlopen(req)

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
        return urllib2.urlopen(req)

    def add_appliance_repositories(self, id, xml_string=None, xml_file=None):
        """PUT /api/v1/user/appliances/<id>/repositories

            Arguments:

                id - Id of the appliance
                xml_string - repositories xml to upload
                xml_file - file object for xml repositories

            Update the list of repositories of the appliance with id id.

            Note: Only the repository ids of the put xml are considered.
        """
        if xml_string and xml_file:
            raise ValueError, "only use one of xml_string or xml_file, not both"

        if xml_file:
            xml_string = xml_file.read()

        url = self.api_addr+'/user/appliances/%s/repositories' % id
        req = HTTPPutRequest(url=url, data=xml_string,
            headers={'Content-Type': 'application/xml'})
        return urllib2.urlopen(req)

    def add_appliance_repository(self, id, repo_id):
        """POST /api/v1/user/appliances/<id>/cmd/add_repository?repo_id=<repo_id>

            Arguments:

                id - Id of the appliance
                repo_id - Id of the repository.

            Add the specified repository to the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/add_repository' % id
        data = urllib.urlencode({"repo_id":repo_id})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def remove_appliance_repository(self, id, repo_id):
        """POST /api/v1/user/appliances/<id>/cmd/remove_repository?repo_id=<repo_id>

            Arguments:

                id - Id of the appliance
                repo_id - Id of the repository.

            Remove the specified repository from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/remove_repository' % id
        data = urllib.urlencode({'repo_id':repo_id})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def add_appliance_user_repository(self, id):
        """POST /api/v1/user/appliances/<id>/cmd/add_user_repository

            Arguments:

                id - Id of the appliance

            Adds the according user repository (the one containing the uploaded RPMs) to the appliance.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/add_user_repository' % id
        req = HTTPPostRequest(url)
        return urllib2.urlopen(req)

    ##############################################################################
    # Software
    ##############################################################################
    def get_appliance_software(self, id):
        """GET /api/v1/user/appliances/<id>/software

            Arguments:

                id - Id of the appliance

            List all selected packages and patterns of the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/software' % id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def set_appliance_software(self, id, xml_string=None, xml_file=None):
        """PUT /api/v1/user/appliances/<id>/software

            Arguments:

                id - Id of the appliance

            Update the list of selected packages and patterns of the appliance with id id.
        """
        if xml_string and xml_file:
            raise ValueError, "only use one of xml_string or xml_file, not both"

        if xml_file:
            xml_string = xml_file.read()

        url = self.api_addr+'/user/appliances/%s/software' % id
        req = HTTPPutRequest(url, data=xml_string,
            headers={'Content-Type': 'application/xml'})
        return urllib2.urlopen(req)

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
        query = urllib.urlencode({'buildid':build_id})
        url = self.api_addr+'/user/appliances/%s/installed?%s' % (id, query)
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def add_appliance_software_package(self, id, name, version='', repository_id=''):
        """POST /api/v1/user/appliances/<id>/cmd/add_package?name=<name>&version=<version>&repository_id=<repo_id>

            Arguments:

                id - Id of the appliance
                name - Name of the package.
                version (optional) - Version of the package.
                repository_id (optional) - Repository to pick the package from.

            Add the specified package to the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/add_package' % id
        data = urllib.urlencode({'name':name, 'version':version,
            'repository_id':repository_id})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def remove_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/remove_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Remove the specified package from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/remove_package' % id
        data = urllib.urlencode({"name":name})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def add_appliance_software_pattern(self, id, name, version='', repository_id=''):
        """POST /api/v1/user/appliances/<id>/cmd/add_pattern?name=<name>&version=<version>&repository_id=<repo_id>

            Arguments:

                id - Id of the appliance
                name - Name of the pattern.
                version (optional) - Version of the pattern.
                repository_id (optional) - Repository to pick the pattern from.

            Add the specified pattern to the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/add_pattern' % id
        data = urllib.urlencode({'name':name, 'version':version,
            'repository_id':repository_id})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def remove_appliance_software_pattern(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/remove_pattern?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the pattern.

            Remove the specified pattern from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/remove_pattern' % id
        data = urllib.urlencode({'name':name})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def ban_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/ban_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Ban a package from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/ban_package' % id
        data = urllib.urlencode({"name":name})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def unban_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/unban_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Unban a package from the appliance with id id.
        """
        url = self.api_addr+'/user/appliances/%s/cmd/unban_package' % id
        data = urllib.urlencode({"name":name})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def search_appliance_software(self, id, q, all_fields=False, all_repos=False):
        """GET /api/v1/user/appliances/<id>/software/search?q=<search_string>&all_fields=<all_fields>&all_repos=<all_repos>

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
        query = urllib.urlencode({'q':q, 'all_fields':all_fields,
            'all_repos':all_repos})
        url = self.api_addr+'/user/appliances/%s/software/search?%s' % (id, query)
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

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
        query = urllib.urlencode({'build_id':build_id, 'path':path})
        url = self.api_addr+'/user/appliances/%s/image_files?%s' % (id, query)
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    ############################################################################
    # GPG Keys
    #############################################################################
    def get_appliance_gpg_keys(self, id):
        """GET /api/v1/user/appliances/<id>/gpg_keys

            Arguments:

                id - Id of the appliance.

            Lists all GPG keys of the appliance with the id id.
        """
        url = self.api_addr+'/user/appliances/%s/gpg_keys' % id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def get_appliance_gpg_key(self, id, key_id):
        """GET /api/v1/user/appliances/<id>/gpg_keys/<key_id>

            Arguments:

                id - Id of the appliance.
                key_id - Id of the GPG key.

            Shows information on the GPG key with the id key_id.
        """
        url = self.api_addr+'/user/appliances/%s/gpg_keys/%s' % (id, key_id)
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def upload_appliance_gpg_key(self, id, name, target, key='', key_file=None):
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
            raise ValueError, "only use one of key or key_file, not both"
        
        url = self.api_addr+'/user/appliances/%s/gpg_keys' % id
        if key:
            data = urllib.urlencode({'name':name, 'target':target, 'key':key})
        elif key_file:
            data = {'name':name, 'target':target, 'file':key_file }
        else:
            raise ValueError, "no key or key_file specified"

        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def delete_appliance_gpg_key(self, id, key_id):
        """DELETE /api/v1/user/appliances/<id>/gpg_keys/<key_id>

            Arguments:

                id - Id of the appliance.
                key_id - Id of the GPG key.

            Deletes the GPG key with the id key_id from the appliance.
        """
        url = self.api_addr+'/user/appliances/%s/gpg_keys/%s' % (id, key_id)
        req = HTTPDeleteRequest(url)
        return urllib2.urlopen(req)

    ########################################################################
    # Overlay files
    ########################################################################
    def get_appliance_overlay_files(self, id):
        """GET /api/v1/user/files?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all overlay files of appliance with id id.
        """
        url = self.api_addr+'/user/files?%s' % urllib.urlencode({'appliance_id':id})
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def add_appliance_overlay_file(self, id, overlay_file=None, filename='',
        path='', owner='', group='', permissions='', enabled='', file_url=''):
        """POST /api/v1/user/files?appliance_id=<id>&filename=<name>&path=<path>&owner=<owner>&group=<group>&permissions=<perms>&enabled=<enabled>&url=<url>

            Arguments:

                appliance_id - Id of the appliance.
                overlay_file - file object to upload
                filename (optional) - The name of the file in the filesystem.
                path (optional) - The path where the file will be stored.
                owner (optional) - The owner of the file.
                group (optional) - The group of the file.
                permissions (optional) - The permissions of the file.
                enabled (optional) - Used to enable/disable this file for the
                                     builds.
                file_url (optional) - The url of the file to add from the internet
                                 (HTTP and FTP are supported) when using the web
                                 upload method

            Adds a file to the appliance with id id.
            Files can either be uploaded in the body of the POST request or from
            a URL in the web:

            With direct uploads the file is expected to be wrapped as with
            form-based file uploads in HTML (RFC 1867) in the body of the POST
            request as the file parameter.

            For Uploads from the web you have to provide the url parameter.

            Optionally, one or more metadata settings can be specified. If those
            are left out, they can also be change later (see below).
        """
        if overlay_file and fileurl:
            raise ValueError, "use overlay_file or fileurl, not both"
        
        data = {'appliance_id':id,
            'filename':filename,
            'path':path,
            'owner':owner,
            'group':group,
            'permissions':permissions,
            'enabled':enabled}

        if file_url:
            data['url'] = fileurl
        elif overlay_file:
            data['file'] = overlay_file
        else
            raise ValueError, "fileurl or overlay_file was invalid"

        url = self.api_addr+'/user/files'
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def get_overlay_file(self, file_id):
        """GET /api/v1/user/files/<file_id>/data

            Arguments:

                file_id - Id of the file.

            Returns the file with id file_id.
        """
        url = self.api_addr+'/user/files/%s/data' % file_id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def add_overlay_file(self, file_id, input_file):
        """PUT /api/v1/user/files/<file_id>/data

            Arguments:

                file_id - Id of the file.

            Writes the content of the file with id file_id.
            The file is expected to be wrapped as with form-based file uploads
            in HTML (RFC 1867) in the body of the PUT request as the file
            parameter.
        """
        url = self.api_addr + 'user/files/%s/data' % file_id
        data = { 'file': input_file }
        req = HTTPPutRequest(url, data)
        return urllib2.urlopen(req)

    def get_overlay_file_metadata(self, id):
        """GET /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.

            Returns the meta data of the file with id file_id.
        """
        url = self.api_addr+'/user/files/%s' % id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def add_overlay_file_metadata(self, file_id, xml_file):
        """PUT /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.
                xml_file - xml metadata to associate to file

            Writes the meta data of the file with id file_id.
        """
        data = {'file':xml_file}
        url = self.api_addr+'/user/files/%s/data' % file_id
        req = HTTPPutRequest(url, data)
        return urllib2.urlopen(req)

    def delete_overlay_file(self, id):
        """DELETE /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.

            Delete the file with id file_id and its meta data.
        """
        url = self.api_addr+'/user/files/%s' % id
        req = HTTPDeleteRequest(url)
        return urllib2.urlopen(req)

    #####################################################################
    # Running builds
    #####################################################################
    def get_running_appliance_builds(self, appliance_id):
        """GET /api/v1/user/running_builds?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all running builds for the appliance with id id.
        """
        query = urllib.urlencode({'appliance_id':appliance_id})
        url = self.api_addr+'/user/running_builds?%s' % query
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def get_build_status(self, build_id):
        """GET /api/v1/user/running_builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Show status of the build with id build_id.
        """
        url = self.api_addr+'/user/running_builds/%s' % build_id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def add_build(self, appliance_id, force='', version='', image_type=''):
        """POST /api/v1/user/running_builds?appliance_id=<id>&force=<force>&version=<version>&image_type=<type>&multi=<multi>

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
        data = urllib.urlencode({'appliance_id':id, 'force':force,
            'version':version, 'image_type':image_type})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def cancel_build(self, build_id):
        """DELETE /api/v1/user/running_builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Cancel build with id build_id.
        """
        url = self.api_addr+'/user/running_builds/%s' % build_id
        req = HTTPDeleteRequest(url)
        return urllib2.urlopen(req)

    ###############################################################
    # Finished builds
    ###############################################################
    def get_completed_builds(self, appliance_id):
        """GET /api/v1/user/builds?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all completed builds for the appliance with id id.
        """
        url = self.api_addr+'/user/builds?%s' % urllib.urlencode({"appliance_id":id})
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def get_build_info(self, build_id):
        """GET /api/v1/user/builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Show build info of the build with id build_id.
        """
        url = self.api_addr+'/user/builds/%s' % build_id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def delete_build(self, build_id):
        """DELETE /api/v1/user/builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Delete build with id build_id.
        """
        url = self.api_addr+'/user/builds/%s' % build_id
        req = HTTPDeleteRequest(url)
        return urllib2.urlopen(req)

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
        query = urllib.urlencode({'base_system':base_system})
        url = self.api_addr+'/user/rpms?%s' % query
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def get_rpm_info(self, rpm_id):
        """GET /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Show information on the uploaded RPM with id rpm_id.
        """
        url = self.api_addr+'/user/rpms/%s' % rpm_id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def get_rpm(self, rpm_id):
        """GET /api/v1/user/rpms/<rpm_id>/data

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Returns the RPM with id rpm_id.
        """
        url = self.api_addr+'/user/rpms/%s/data' % rpm_id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def upload_rpm(self, base_system, rpm_file):
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
        data = { 'base_system':base_system, 'file':rpm_file }
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(url, data).read()

    def update_rpm(self, rpm_id, rpm_file):
        """PUT /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Update the content of the RPM or archive with the id rpm_id.
            The file is expected to be wrapped as with form-based file uploads
            in HTML (RFC 1867) in the body of the POST request as the file
            parameter.
        """
        url = self.api_addr+'/user/rpms/%s' % rpm_id
        data = { 'file':rpm_file }
        req = HTTPPutRequest(url, data)
        return urllib2.urlopen(req)

    def delete_rpm(self, rpm_id):
        """DELETE /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Deletes the RPM or archive with the id rpm_id from the user
            repository.
        """
        url = self.api_addr+'/user/rpms/%s' % rpm_id
        req = HTTPDeleteRequest(url)
        return urllib2.urlopen(req)

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
        query = urllib.urlencode(criteria)
        url = self.api_addr+'/user/repositories?%s' % query
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    def import_repository(self, repo_url, name):
        """POST /api/v1/user/repositories?url=<url>&name=<name>

            Arguments:

                url - Base url of the repository.
                name - Name for the repository.

            Imports a new repository into Studio. Returns the metadata for the created repository.
        """
        url = self.api_addr+'/user/repositories'
        data = urllib.urlencode({'url':repo_url, 'name':name})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)

    def get_repository_info(self, repo_id):
        """GET /api/v1/user/repositories/<id>

            Arguments:

                id - Id of the repository.

            Show information on the repository with the id id.
        """
        url = self.api_addr+'/user/repositories/%s' % repo_id
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

    ####################################################################
    # Testdrives
    ####################################################################
    def get_testdrives(self):
        """GET /api/v1/user/testdrives

            Returns a list of running testdrives.
        """
        url = self.api_addr + '/user/testdrives'
        req = HTTPGetRequest(url)
        return urllib2.urlopen(req)

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
        data = urllib.urlencode({'build_id':build_id})
        req = HTTPPostRequest(url, data)
        return urllib2.urlopen(req)


class StudioUtils:
    @staticmethod
    def get_appliance_fragment():
        template = """

        """

    @staticmethod
    def get_build_fragment():
        template = """
        
        """

    @staticmethod
    def get_repository_fragment():
        template = """
        
        """
                
    @staticmethod
    def get_file_metadata_fragment():
        template = """
        
        """



####
# 02/2006 Will Holcomb <wholcomb@gmail.com>
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# 7/26/07 Slightly modified by Brian Schneider  
# in order to support unicode files ( multipart_encode function )
#
# 02 Jan 2012 Chris Horler
#  - minor modifications
# 

import mimetools, mimetypes
import os, stat

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

# Controls how sequences are uncoded. If true, elements may be given multiple values by
#  assigning a sequence.
doseq = 1

class MultipartPostHandler(urllib2.BaseHandler):
    """MultipartPostHandler(urllib2.BaseHandler)

Usage:
  Enables the use of multipart/form-data for posting forms

Inspirations:
  Upload files in python:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306
  urllib2_file:
    Fabien Seisen: <fabien@seisen.org>

Example:
  import MultipartPostHandler, urllib2, cookielib

  cookies = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
  params = { "username" : "bob", "password" : "riviera",
             "file" : open("filename", "rb") }
  opener.open("http://wwww.bobsite.com/upload/", params)
    """
    handler_order = urllib2.HTTPHandler.handler_order - 10 # needs to run first

    def http_request(self, request):
        data = request.get_data()
        if data and not isinstance(data, str):
            v_files = []
            v_vars = []
            try:
                for (key, value) in data.items():
                    if isinstance(value, file):
                        v_files.append((key, value))
                    else:
                        v_vars.append((key, value))
            except TypeError:
                systype, value, traceback = sys.exc_info()
                raise TypeError, "not a valid non-string sequence or mapping object", traceback

            if len(v_files) == 0:
                data = urllib.urlencode(v_vars, doseq)
            else:
                boundary, data = self.multipart_encode(v_vars, v_files)

                contenttype = 'multipart/form-data; boundary=%s' % boundary
                if(request.has_header('Content-Type')
                    and request.get_header('Content-Type').find('multipart/form-data') != 0):
                    print "Replacing %s with %s" % (request.get_header('content-type'), 'multipart/form-data')
                request.add_unredirected_header('Content-Type', contenttype)

            request.add_data(data)

        return request

    @staticmethod
    def multipart_encode(vars, files, boundary = None, buf = None):
        if not boundary:
            boundary = mimetools.choose_boundary()
        if not buf:
            buf = StringIO()
        for(key, value) in vars:
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"' % key)
            buf.write('\r\n\r\n' + value + '\r\n')
        for(key, fd) in files:
            #file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
            filename = fd.name.split('/')[-1]
            contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
            buf.write('Content-Type: %s\r\n' % contenttype)
            # buffer += 'Content-Length: %s\r\n' % file_size
            fd.seek(0)
            buf.write('\r\n' + fd.read() + '\r\n')
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        return boundary, buf

    https_request = http_request
