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

def stop():
  ctx.logger.info("stopping codeserver")
  # create directory for serving code and load it up
  pid=ctx.instance.runtime_properties['pid']
  os.system("kill {}".format(pid))
  os.system("rm -rf /tmp/code")
  ctx.logger.info("stop complete")

stop()
