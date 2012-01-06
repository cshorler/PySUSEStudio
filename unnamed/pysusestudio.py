#!/usr/bin/env python

# TODO: self.authenticated is not needed - if there is an authentication error propagate
# an exception instead, it's a much cleaner solution
# TODO: rewrite to use standard library urllib2 for all http exchanges?
# - rather than non-standard httplib2?
# TODO: for all functions creating data - probably we should parse the return code to know if it was successful if it comes via HTML?
    
"""

"""

__license__ = 'GPL v.2 http://www.gnu.org/licenses/gpl.txt'
__author__ = "Chris Horler <cshorler@googlemail.com>"
__version__ = '1.0-pre1'


import urllib
import urllib2

from urlparse import urlparse
from urllib2 import HTTPError

from MultipartPostHandler import MultipartPostHandler

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

class pySuseStudioError(Exception):
    def __init__(self, msg, error_code=None):
        self.msg = msg
        if error_code == 400:
            raise APILimit(msg)
    def __str__(self):
        return repr(self.msg)

class APILimit(pySuseStudioError):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class AuthError(pySuseStudioError):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class SuseStudio:
    """Suse Studio REST API client implementation"""
    def __init__(self, username = None, password = None, headers = None,
        host = 'http://susestudio.com'):
        """pySuseStudio( username = None, password = None, headers = None)

            Instantiates an instance of pySuseStudio. Takes optional parameters
            for authentication and such (see below).

            Parameters:
                username - Your Suse Studio username, if you want Basic (HTTP)
                Authentication.

                password - Your Suse Studio secret key, if you want Basic (HTTP)
                Authentication.

                headers - User agent header.
        """
        self.host = host.rstrip('/')
        self.address = self.host + '/api/v1'
        
        self.authenticated = False
        self.username = username
        self.password = password

        # get address for authentication
        auth_addr = urlparse(self.address)
        auth_address = str(auth_addr.scheme) +'://'+ str(auth_addr.netloc)

        # Check and set up authentication
        if self.username and self.password:
            # Assume Basic authentication ritual
            auth_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            auth_manager.add_password(None, auth_address, self.username,
                                      self.password)
            handler = urllib2.HTTPBasicAuthHandler(auth_manager)
            opener = urllib2.build_opener(handler, MultipartPostHandler, urllib2.HTTPHandler(debuglevel=1))
            if headers:
                opener.addheaders = [('User-agent', headers)]
            urllib2.install_opener(opener)

            try:
                self.authenticated = True
            except HTTPError, e:
                raise pySuseStudioError("Authentication failed with your provided credentials."
                    + "Try again? (%s failure)" % `e.code`, e.code)

    ###############################################################
    # GENERAL INFORMATION
    ################################################################
    def get_api_key(self):
        """GET /user/show_api_key

            Returns an HTML page which contains the API key flagged as:

            <span class="studio:api_key">ksdjfu93r</span>
        """
        try:
            if self.authenticated:
                return urllib2.urlopen(self.host+'/user/show_api_key').read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on your account.")
        except HTTPError, e:
            raise pySuseStudioError("getApiKey() failed with a %s error code." % `e.code`)

    def get_account(self):
        """GET /api/v1/user/account

             Returns information about the account, such as username, email address and disk quota.
        """
        try:
            if self.authenticated:
                return urllib2.urlopen(self.address+'/user/account').read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on your account.")
        except HTTPError, e:
            raise pySuseStudioError("It seems that there's something wrong. You got %s error code"
                + "are you doing something you shouldn't be?" % `e.code`, e.code)

    def get_api_version(self):
        """GET /api/v1/user/api_version

            Returns the running API version including the minor version.
        """
        try:
            if self.authenticated:
                return urllib2.urlopen(self.address+'/user/api_version').read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on your account.")
        except HTTPError, e:
            raise pySuseStudioError("getApiVersion() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                query = urllib.urlencode({'name':name})
                url = self.address + '/user/template_sets/?%s' % query

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on template sets.")
        except HTTPError, e:
            raise pySuseStudioError("getTemplateSets() failed with a %s error code." % `e.code`)

    ############################################################
    # Appliances
    ###########################################################
    def get_appliances(self, id=''):
        """GET /api/v1/user/appliances
        GET /api/v1/user/appliances/<id>/status

            List all appliances of the current user.
            or
            Show details of appliance with id id.
            
            Arguments:

                id - Id of the appliance
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances'
                if id:
                    url = url + '/%s' % id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on appliances.")
        except HTTPError, e:
            raise pySuseStudioError("getAppliances() failed with a %s error code." % `e.code`)

    def get_appliance_status(self, id):
        """TODO:
            
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/status' % id
                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on appliances.")
        except HTTPError, e:
            raise pySuseStudioError("getAppliances() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                url = self.address+'/user/appliances'
                data = urllib.urlencode({'clone_from':clone_from, 'name':name, 'arch':arch})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on appliances.")
        except HTTPError, e:
            raise pySuseStudioError("setAppliances() failed with a %s error code." % `e.code`)

    def delete_appliance(self, id):
        """DELETE /api/v1/user/appliances/<id>

            Arguments:

                id - Id of the appliance

            Delete appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s' % id
                return urllib2.urlopen(HTTPDeleteRequest(url)).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on appliances.")
        except HTTPError, e:
            raise pySuseStudioError("delAppliances() failed with a %s error code." % `e.code`)

    ##################################################################
    # Repositories
    ##################################################################
    def get_appliance_repositories(self, id):
        """GET /api/v1/user/appliances/<id>/repositories

            Arguments:

                id - Id of the appliance

            List all repositories of the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/repositories' % id
                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on Repositories.")
        except HTTPError, e:
            raise pySuseStudioError("getRepositories() failed with a %s error code." % `e.code`)

    def add_appliance_repositories(self, id, xml_string=None, xml_file=None):
        """PUT /api/v1/user/appliances/<id>/repositories

            Arguments:

                id - Id of the appliance

            Update the list of repositories of the appliance with id id.

            Note: Only the repository ids of the put xml are considered.
        """
        try:
            if self.authenticated:
                if xml_string and xml_file:
                    raise pySuseStudioError("please only use a string or file")

                if xml_file:
                    xml_string = open(xml_file, 'r').read()

                if xml_string:
                    url = self.address+'/user/appliances/%s/repositories' % id
                    req = HTTPPutRequest(url=url, data=xml_string, headers={'Content-Type': 'application/xml'})
                    return urllib2.urlopen(req).read()
            else:
                raise pySuseStudioError("You need to be authenticated to put info on Repositories.")
        except HTTPError, e:
            raise pySuseStudioError("putRepositories() failed with a %s error code." % `e.code`)

    def add_appliance_repository(self, id, repo_id):
        """POST /api/v1/user/appliances/<id>/cmd/add_repository?repo_id=<repo_id>

            Arguments:

                id - Id of the appliance
                repo_id - Id of the repository.

            Add the specified repository to the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/add_repository' % id
                data = urllib.urlencode({"repo_id":repo_id})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to insert new Repositories.")
        except HTTPError, e:
            raise pySuseStudioError("setRepositories() failed with a %s error code." % `e.code`)

    def remove_appliance_repository(self, id, repo_id):
        """POST /api/v1/user/appliances/<id>/cmd/remove_repository?repo_id=<repo_id>

            Arguments:

                id - Id of the appliance
                repo_id - Id of the repository.

            Remove the specified repository from the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/remove_repository' % id
                data = urllib.urlencode({'repo_id':repo_id})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to remove Repositories.")
        except HTTPError, e:
            raise pySuseStudioError("delRepositories() failed with a %s error code." % `e.code`)

    def add_appliance_user_repository(self, id):
        """POST /api/v1/user/appliances/<id>/cmd/add_user_repository

            Arguments:

                id - Id of the appliance

            Adds the according user repository (the one containing the uploaded RPMs) to the appliance.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/add_user_repository' % id
                #TODO: I put a space, would it work without? (needs to be HTTP POST)
                return urllib2.urlopen(url, ' ').read()
            else:
                raise pySuseStudioError("You need to be authenticated to add user to Repository.")
        except HTTPError, e:
            raise pySuseStudioError("addRepositoryUser() failed with a %s error code." % `e.code`)

    ##############################################################################
    # Software
    ##############################################################################
    def get_appliance_software(self, id):
    #def getSoftware(self, id):
        """GET /api/v1/user/appliances/<id>/software

            Arguments:

                id - Id of the appliance

            List all selected packages and patterns of the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/software' % id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on software.")
        except HTTPError, e:
            raise pySuseStudioError("getSoftware() failed with a %s error code." % `e.code`)

    def set_appliance_software(self, id, xml_string=None, xml_file=None):
        """PUT /api/v1/user/appliances/<id>/software

            Arguments:

                id - Id of the appliance

            Update the list of selected packages and patterns of the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/software' % id
                if xml_string and xml_file:
                    raise pySuseStudioError("dont use xml_string and xml_file together")
                if xml_file:
                    xml_string = xml_file.read()

                req = HTTPPutRequest(url, data=xml_string, headers={'Content-Type': 'application/xml'})
                return urllib2.urlopen(req).read()
            else:
                raise pySuseStudioError("You need to be authenticated to put info.")
        except HTTPError, e:
            raise pySuseStudioError("putSoftware() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                query = urllib.urlencode({'buildid':build_id})
                url = self.address+'/user/appliances/%s/installed?%s' % (id, query)

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on installed software.")
        except HTTPError, e:
            raise pySuseStudioError("getSoftwareInstalled() failed with a %s error code." % `e.code`)

    def add_appliance_software_package(self, id, name, version='', repository_id=''):
        """POST /api/v1/user/appliances/<id>/cmd/add_package?name=<name>&version=<version>&repository_id=<repo_id>

            Arguments:

                id - Id of the appliance
                name - Name of the package.
                version (optional) - Version of the package.
                repository_id (optional) - Repository to pick the package from.

            Add the specified package to the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/add_package' % id
                data = urllib.urlencode({'name':name, 'version':version,
                    'repository_id':repository_id})
                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to add package to Repository.")
        except HTTPError, e:
            raise pySuseStudioError("addSoftwarePackage() failed with a %s error code." % `e.code`)

    def remove_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/remove_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Remove the specified package from the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/remove_package' % id
                data = urllib.urlencode({"name":name})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to remove package from Repository.")
        except HTTPError, e:
            raise pySuseStudioError("delSoftwarePackage() failed with a %s error code." % `e.code`)


    def add_appliance_software_pattern(self, id, name, version='', repository_id=''):
        """POST /api/v1/user/appliances/<id>/cmd/add_pattern?name=<name>&version=<version>&repository_id=<repo_id>

            Arguments:

                id - Id of the appliance
                name - Name of the pattern.
                version (optional) - Version of the pattern.
                repository_id (optional) - Repository to pick the pattern from.

            Add the specified pattern to the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/add_pattern' % id
                data = urllib.urlencode({'name':name, 'version':version,
                    'repository_id':repository_id})
                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to add pattern to Repository.")
        except HTTPError, e:
            raise pySuseStudioError("addSoftwarePattern() failed with a %s error code." % `e.code`)

    def remove_appliance_software_pattern(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/remove_pattern?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the pattern.

            Remove the specified pattern from the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/remove_pattern' % id
                data = urllib.urlencode({'name':name})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to remove pattern from Repository.")
        except HTTPError, e:
            raise pySuseStudioError("delSoftwarePattern() failed with a %s error code." % `e.code`)

    def ban_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/ban_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Ban a package from the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/ban_package' % id
                data = urllib.urlencode({"name":name})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to ban package from appliance.")
        except HTTPError, e:
            raise pySuseStudioError("banSoftwarePackage() failed with a %s error code." % `e.code`)

    def unban_appliance_software_package(self, id, name):
        """POST /api/v1/user/appliances/<id>/cmd/unban_package?name=<name>

            Arguments:

                id - Id of the appliance
                name - Name of the package.

            Unban a package from the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/cmd/unban_package' % id
                data = urllib.urlencode({"name":name})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to unban package from appliance.")
        except HTTPError, e:
            raise pySuseStudioError("unbanSoftwarePackage() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                query = urllib.urlencode({'q':q, 'all_fields':all_fields, 'all_repos':all_repos})
                url = self.address+'/user/appliances/%s/software/search?%s' % (id, query)

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to search software in a Repository.")
        except HTTPError, e:
            raise pySuseStudioError("searchSoftware() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                query = urllib.urlencode({'build_id':build_id, 'path':path})
                url = self.address+'/user/appliances/%s/image_files?%s' % (id, query)

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get files from an image.")
        except HTTPError, e:
            raise pySuseStudioError("getImageFiles() failed with a %s error code." % `e.code`)

    ############################################################################
    # GPG Keys
    #############################################################################
    def get_appliance_gpg_keys(self, id):
        """GET /api/v1/user/appliances/<id>/gpg_keys

            Arguments:

                id - Id of the appliance.

            Lists all GPG keys of the appliance with the id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/gpg_keys' % id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get GPG keys from an appliance.")
        except HTTPError, e:
            raise pySuseStudioError("getGPGKeys() failed with a %s error code." % `e.code`)

    def get_appliance_gpg_key(self, id, key_id):
        """GET /api/v1/user/appliances/<id>/gpg_keys/<key_id>

            Arguments:

                id - Id of the appliance.
                key_id - Id of the GPG key.

            Shows information on the GPG key with the id key_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/gpg_keys/%s' % (id, key_id)

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info from a GPG key.")
        except HTTPError, e:
            raise pySuseStudioError("getGPGKey() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/gpg_keys' % id
                if key:
                    data = urllib.urlencode({'name':name, 'target':target, 'key':key})
                elif key_file:
                    data = {'name':name, 'target':target, 'file':key_file }
                else:
                    raise pySuseStudioError("inputs error")

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to set a GPG Key for an appliance.")
        except HTTPError, e:
            raise pySuseStudioError("setGPGKey() failed with a %s error code." % `e.code`)


    def delete_appliance_gpg_key(self, id, key_id):
        """DELETE /api/v1/user/appliances/<id>/gpg_keys/<key_id>

            Arguments:

                id - Id of the appliance.
                key_id - Id of the GPG key.

            Deletes the GPG key with the id key_id from the appliance.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/appliances/%s/gpg_keys/%s' % (id, key_id)
                return urllib2.urlopen(HTTPDeleteRequest(url)).read()
            else:
                raise pySuseStudioError("You need to be authenticated to delete a GPG key.")
        except HTTPError, e:
            raise pySuseStudioError("delGPGKey() failed with a %s error code." % `e.code`)

    ########################################################################
    # Overlay files
    ########################################################################
    def get_appliance_overlay_files(self, id):
        """GET /api/v1/user/files?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all overlay files of appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/files?%s' % urllib.urlencode({'appliance_id':id})
                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on overlay files.")
        except HTTPError, e:
            raise pySuseStudioError("getOverlayFiles() failed with a %s error code." % `e.code`)

    def add_appliance_overlay_file(self, id, body='', filename='', path='', owner='', group='',
        permissions='', enabled='', fileurl=''):
        """POST /api/v1/user/files?appliance_id=<id>&filename=<name>&path=<path>&owner=<owner>&group=<group>&permissions=<perms>&enabled=<enabled>&url=<url>

            Arguments:

                appliance_id - Id of the appliance.
                filename (optional) - The name of the file in the filesystem.
                path (optional) - The path where the file will be stored.
                owner (optional) - The owner of the file.
                group (optional) - The group of the file.
                permissions (optional) - The permissions of the file.
                enabled (optional) - Used to enable/disable this file for the
                                     builds.
                url (optional) - The url of the file to add from the internet
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
        try:
            if self.authenticated:
                data = {'appliance_id':id,
                    'filename':filename,
                    'path':path,
                    'owner':owner,
                    'group':group,
                    'permissions':permissions,
                    'enabled':enabled}

                if fireurl:
                    data['url'] = fileurl
                else:
                    data['file'] = body

                if fileurl and body:
                    raise pySuseStudioError("Invalid to specify both fileurl and body parameter")

                url = self.address+'/user/files'
                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to add overlay files to Repository.")
        except HTTPError, e:
            raise pySuseStudioError("addOverlayFiles failed with a %s error code." % `e.code`)

    def get_overlay_file(self, file_id):
        """GET /api/v1/user/files/<file_id>/data

            Arguments:

                file_id - Id of the file.

            Returns the file with id file_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/files/%s/data' % file_id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to set requested overlay file.")
        except HTTPError, e:
            raise pySuseStudioError("getOverlayFile() failed with a %s error code." % `e.code`)

    def add_overlay_file(self, file_id, input_file):
        """PUT /api/v1/user/files/<file_id>/data

            Arguments:

                file_id - Id of the file.

            Writes the content of the file with id file_id.
            The file is expected to be wrapped as with form-based file uploads
            in HTML (RFC 1867) in the body of the PUT request as the file
            parameter.
        """
        try:
            if self.authenticated:
                url = self.address + 'user/files/%s/data' % file_id
                data = { 'file': input_file }

                req = HTTPPutRequest(url, data)
                return urllib2.urlopen(req).read()
            else:
                raise pySuseStudioError("You need to be authenticated to put file.")
        except HTTPError, e:
            raise pySuseStudioError("putOverlayFile() failed with a %s error code." % `e.code`)

    def get_overlay_file_metadata(self, id):
        """GET /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.

            Returns the meta data of the file with id file_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/files/'+str(id)

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to set metadata on requested overlay file.")
        except HTTPError, e:
            raise pySuseStudioError("getOverlayFileMeta() failed with a %s error code." % `e.code`)

    def add_overlay_file_metadata(self, id, body):
        """PUT /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.

            Writes the meta data of the file with id file_id.
        """
        try:
            if self.authenticated:
                data = {'file':body}
                url = self.address+'/user/files/%s/data' % id
                return urllib2.urlopen(HTTPPutRequest(url, data)).read()
            else:
                raise pySuseStudioError("You need to be authenticated to put file.")
        except HTTPError, e:
            raise pySuseStudioError("putOverlayFile() failed with a %s error code." % `e.code`)

    def delete_overlay_file(self, id):
        """DELETE /api/v1/user/files/<file_id>

            Arguments:

                file_id - Id of the file.

            Delete the file with id file_id and its meta data.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/files/%s' % id
                return urllib2.urlopen(HTTPDeleteRequest(url)).read()
            else:
                raise pySuseStudioError("You need to be authenticated to remove overlay file.")
        except HTTPError, e:
            raise pySuseStudioError("delOverlayFile() failed with a %s error code." % `e.code`)

    #####################################################################
    # Running builds
    #####################################################################
    def get_running_appliance_builds(self, appliance_id):
        """GET /api/v1/user/running_builds?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all running builds for the appliance with id id.
        """
        try:
            if self.authenticated:
                query = urllib.urlencode({'appliance_id':appliance_id})
                url = self.address+'/user/running_builds?%s' % query

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to list running builds for a selected appliance.")
        except HTTPError, e:
            raise pySuseStudioError("getRunningBuilds() failed with a %s error code." % `e.code`)

    def get_build_status(self, build_id):
        """GET /api/v1/user/running_builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Show status of the build with id build_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/running_builds/%s' % build_id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get status on requested build.")
        except HTTPError, e:
            raise pySuseStudioError("getRunningBuild() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                url = self.address+'/user/running_builds'
                data = urllib.urlencode({'appliance_id':id, 'force':force, 'version':version,
                    'image_type':image_type})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to start a new build.")
        except HTTPError, e:
            raise pySuseStudioError("addBuild failed with a %s error code." % `e.code`)

    def cancel_build(self, build_id):
        """DELETE /api/v1/user/running_builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Cancel build with id build_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/running_builds/%s' % build_id
                req = HTTPDeleteRequest(url)

                return urllib2.urlopen(req).read()
            else:
                raise pySuseStudioError("You need to be authenticated to remove running build.")
        except HTTPError, e:
            raise pySuseStudioError("delRunningBuild() failed with a %s error code." % `e.code`)

    ###############################################################
    # Finished builds
    ###############################################################
    def get_completed_builds(self, appliance_id):
        """GET /api/v1/user/builds?appliance_id=<id>

            Arguments:

                appliance_id - Id of the appliance.

            List all completed builds for the appliance with id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/builds?%s' % urllib.urlencode({"appliance_id":id})

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to list completed builds for a selected appliance.")
        except HTTPError, e:
            raise pySuseStudioError("getCompletedBuilds() failed with a %s error code." % `e.code`)

    def get_build_info(self, build_id):
        """GET /api/v1/user/builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Show build info of the build with id build_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/builds/%s' % build_id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get status on requested build.")
        except HTTPError, e:
            raise pySuseStudioError("getCompletedBuild() failed with a %s error code." % `e.code`)

    def delete_build(self, build_id):
        """DELETE /api/v1/user/builds/<build_id>

            Arguments:

                build_id - Id of the build.

            Delete build with id build_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/builds/%s' % build_id
                req = HTTPDeleteRequest(url)

                return urllib2.urlopen(req).read()
            else:
                raise pySuseStudioError("You need to be authenticated to remove requested build.")
        except HTTPError, e:
            raise pySuseStudioError("delCompletedBuild() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                query = urllib.urlencode({'base_system':base_system})
                url = self.address+'/user/rpms?%s' % query

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to list all uploaded RPMs for a selected base system.")
        except HTTPError, e:
            raise pySuseStudioError("getRPMs() failed with a %s error code." % `e.code`)

    def get_rpm_info(self, rpm_id):
        """GET /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Show information on the uploaded RPM with id rpm_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/rpms/%s' % rpm_id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get info on requested RPM.")
        except HTTPError, e:
            raise pySuseStudioError("getRPMInfo() failed with a %s error code." % `e.code`)

    def get_rpm(self, rpm_id):
        """GET /api/v1/user/rpms/<rpm_id>/data

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Returns the RPM with id rpm_id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/rpms/%s/data' % rpm_id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get requested RPM.")
        except HTTPError, e:
            raise pySuseStudioError("getRPM() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                url = self.address+'/user/rpms'
                data = { 'base_system':base_system,
                    'file':rpm_file }

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to add a new RPM")
        except HTTPError, e:
            raise pySuseStudioError("addRPM() failed with a %s error code." % `e.code`)

    def update_rpm(self, rpm_id, rpm_file):
        """PUT /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Update the content of the RPM or archive with the id rpm_id.
            The file is expected to be wrapped as with form-based file uploads
            in HTML (RFC 1867) in the body of the POST request as the file
            parameter.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/rpms/%s' % rpm_id
                data = { 'file':rpm_file }

                req = HTTPPutRequest(url, data)
                return urllib2.urlopen(req).read()
            else:
                raise pySuseStudioError("You need to be authenticated to update RPM's content.")
        except HTTPError, e:
            raise pySuseStudioError("putRPM() failed with a %s error code." % `e.code`)

    def delete_rpm(self, rpm_id):
        """DELETE /api/v1/user/rpms/<rpm_id>

            Arguments:

                rpm_id - ID of the uploaded RPM.

            Deletes the RPM or archive with the id rpm_id from the user
            repository.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/rpms/%s' % rpm_id
                req = HTTPDeleteRequest(url)

                return urllib2.urlopen(req).read()
            else:
                raise pySuseStudioError("You need to be authenticated to remove RPM.")
        except HTTPError, e:
            raise pySuseStudioError("delRPM() failed with a %s error code." % `e.code`)

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
        try:
            if self.authenticated:
                criteria = []
                if base_system:
                    criteria.append(('base_system', base_system))
                # FIXME: the search string / filter seems to cause all types of errors
                #if search_string:
                #    criteria.append(('filter', search_string))
                query = urllib.urlencode(criteria)
                url = self.address+'/user/repositories?%s' % query

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to list repositories.")
        except HTTPError, e:
            raise pySuseStudioError("getRepositories() failed with a %s error code." % `e.code`)

    def import_repository(self, repo_url, name):
        """POST /api/v1/user/repositories?url=<url>&name=<name>

            Arguments:

                url - Base url of the repository.
                name - Name for the repository.

            Imports a new repository into Studio. Returns the metadata for the created repository.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/repositories'
                data = urllib.urlencode({'url':repo_url, 'name':name})

                return urllib2.urlopen(url, data).read()
            else:
                raise pySuseStudioError("You need to be authenticated to add a new repository.")
        except HTTPError, e:
            raise pySuseStudioError("addRepository() failed with a %s error code." % `e.code`)

    def get_repository_info(self, repo_id):
        """GET /api/v1/user/repositories/<id>

            Arguments:

                id - Id of the repository.

            Show information on the repository with the id id.
        """
        try:
            if self.authenticated:
                url = self.address+'/user/repositories/%s' % repo_id

                return urllib2.urlopen(url).read()
            else:
                raise pySuseStudioError("You need to be authenticated to get information on requested repository.")
        except HTTPError, e:
            raise pySuseStudioError("getRepository() failed with a %s error code." % `e.code`)

    ####################################################################
    # Testdrives
    ####################################################################
    def get_testdrives(self):
        """GET /api/v1/user/testdrives

            Returns a list of running testdrives.
        """
        try:
            if self.authenticated:
                url = self.address + '/user/testdrives'
                return urllib2.urlopen(url).read()
        except HTTPError, e:
            raise pySuseStudioError("getTestDrives() failed with a %s error code." % e.code)

    def start_testdrive(self, build_id):
        """POST /api/v1/user/testdrives?build_id=<build_id>

            Arguments:

                build_id - Id of the build to run in testdrive.

            Starts a new testdrive session of the given build on the server and
            returns information about how to access it.

            Note: Testdrive sessions will be aborted when no client has
            connected after 60 seconds.
        """
        try:
            if self.authenticated:
                url = self.address + '/user/testdrives'
                data = urllib.urlencode({'build_id':build_id})

                return urllib2.urlopen(url, data).read()
        except HTTPError, e:
            raise pySuseStudioError("getTestDrives() failed with a %s error code." % e.code)

    ####################################################################
    # plugin version
    ####################################################################
    #TODO: really this should redirect to module parameters or be module level?
    def version(self):
        """version()

            Print version information

        """
        try:
            print "pySuseStudio v."+ __version__+" - Author: "+__author__
            print "released under "+ __license__

        except HTTPError, e:
            raise pySuseStudioError("version() failed with a %s error code." % `e.code`)




