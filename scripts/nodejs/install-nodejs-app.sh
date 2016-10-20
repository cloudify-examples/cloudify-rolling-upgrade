#!/bin/bash

set -e

function download() {

   url=$1
   name=$2

   if [ -f "`pwd`/${name}" ]; then
        ctx logger info "`pwd`/${name} already exists, No need to download"
   else
        # download to given directory
        ctx logger info "Downloading ${url} to `pwd`/${name}"

        set +e
        curl_cmd=$(which curl)
        wget_cmd=$(which wget)
        set -e

        if [[ ! -z ${curl_cmd} ]]; then
            curl -L -o ${name} ${url}
        elif [[ ! -z ${wget_cmd} ]]; then
            wget -O ${name} ${url}
        else
            ctx logger error "Failed to download ${url}: Neither 'cURL' nor 'wget' were found on the system"
            exit 1;
        fi
   fi

}

function extract() {

    archive=$1
    destination=$2

    if [ ! -d ${destination} ]; then


       # assuming tarball if the archive is not a zip.
       # we dont check that tar exists since if we made it
       # this far, it definitely exists (nodejs used it)
       ctx logger info "Untaring ${archive}"
       tar -zxvf ${archive}


    fi
}

function version(){
 if [[ $NODEJS_ARCHIVE_NAME =~ -([^-]*)\.[^\.-]+$ ]]; then
   n=${#BASH_REMATCH[*]}
   echo ${BASH_REMATCH[1]}
 fi
}

TEMP_DIR='/tmp'
NODEJS_BINARIES_PATH=$(ctx instance runtime_properties nodejs_binaries_path)
APPLICATION_URL=$(ctx node properties application_url)

if [[ $APPLICATION_URL =~ .*/manager:.* ]]; then
  APPLICATION_URL=$(echo $APPLICATION_URL|sed "s,manager,$MANAGEMENT_IP,g")
fi

AFTER_SLASH=${APPLICATION_URL##*/}
NODEJS_ARCHIVE_NAME=${AFTER_SLASH%%\?*}
APP_VERSION=$(version)

ctx logger info "app_version=$APP_VERSION"
ctx logger info "app url=$APPLICATION_URL"
ctx logger info "nodejs_archive_name=$NODEJS_ARCHIVE_NAME"

NODEJS_ROOT_PATH=${TEMP_DIR}/$(ctx execution-id)/nodejs
NODEJS_SOURCE_PATH=${NODEJS_ROOT_PATH}/nodejs-source
#mkdir -p ${NODEJS_ROOT_PATH}
mkdir -p ${NODEJS_SOURCE_PATH}

cd ${TEMP_DIR}
download ${APPLICATION_URL} ${NODEJS_ARCHIVE_NAME}
cd ${NODEJS_SOURCE_PATH}
tar -xzf ${TEMP_DIR}/${NODEJS_ARCHIVE_NAME}

ctx logger info "Installing nodejs dependencies using npm"
${NODEJS_BINARIES_PATH}/bin/npm install

ctx instance runtime_properties nodejs_source_path ${NODEJS_SOURCE_PATH}

# set version
ctx logger info "Setting app version = ${APP_VERSION}"
ctx instance runtime_properties app_version ${APP_VERSION}

ctx logger info "Sucessfully installed nodejs"
