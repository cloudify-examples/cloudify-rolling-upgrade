#
# Start process that serves code to rolling upgrade process.  In a
# "real" system, this would be external to this blueprint
#
import time
import sys
import os
import subprocess
import traceback
from cloudify import ctx
from cloudify.state import ctx_parameters as p

def start():
  ctx.logger.info("starting codeserver")
  # create directory for serving code and load it up
  os.system("rm -rf /tmp/code")
  ctx.logger.info("creating server directory")
  os.mkdir("/tmp/code")
  ctx.logger.info("downloading resources")
  ctx.download_resource("resources/upgrade-test-1.0.tgz","/tmp/code/upgrade-test-1.0.tgz")
  ctx.download_resource("resources/upgrade-test-1.1.tgz","/tmp/code/upgrade-test-1.1.tgz")
  ctx.logger.info("starting server")

  # start server
  os.chdir("/tmp/code")
  proc=subprocess.Popen(['nohup','python','-m','SimpleHTTPServer','8000'],
                     stdout=open("/tmp/httpserver.out","w"),
                     stderr=open("/tmp/httpserver.err","w"))

  ctx.instance.runtime_properties['pid']=proc.pid
  ctx.logger.info("startup complete")


start()
