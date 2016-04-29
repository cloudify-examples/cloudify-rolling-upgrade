import subprocess
import os.path
from cloudify import ctx
from cloudify import exceptions
from cloudify.state import ctx_parameters as inputs
from cloudify.exceptions import RecoverableError,NonRecoverableError

ctx.logger.info("rollback.py called")

if(not os.path.isfile("/tmp/rollback.tgz")):
  ctx.logger.warning("no previous version found")
else:

  # restore rollback
  src_path=ctx.instance.runtime_properties['nodejs_source_path']
  ret=subprocess.call("cd {};/bin/tar xzf /tmp/rollback.tgz".format(src_path),shell=True)
  if(ret):
    raise RecoverableError("restoration from saved version failed")

  # restart server
  pid=ctx.instance.runtime_properties['pid']

  proc=subprocess.Popen("ps -p {} -h|awk '{}'".format(pid,'{printf "%s %s",$5,$6}'),stdout=subprocess.PIPE,shell=True)
  if(proc.wait()!=0):
    raise RecoverableError("failed getting existing node process info")

  subprocess.call("kill {}".format(pid),shell=True)

  with open("/dev/null","w") as f:
    proc=subprocess.Popen(["nohup","{}/bin/node".format(ctx.instance.runtime_properties['nodejs_binaries_path']),"{}/server.js".format(ctx.instance.runtime_properties['nodejs_source_path'])],stdout=f, stderr=f, env={"NODEJS_PORT":str(ctx.node.properties['port'])})
    # store new pid
    ctx.instance.runtime_properties['pid']=proc.pid

  # restore version #
  ctx.instance.runtime_properties['app_version']=ctx.instance.runtime_properties['app_prev_version']

