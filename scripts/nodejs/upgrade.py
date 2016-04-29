import subprocess
from cloudify import ctx
from cloudify import exceptions
from cloudify.state import ctx_parameters as inputs
from cloudify.exceptions import RecoverableError,NonRecoverableError
from urlparse import urlparse

#
# Utility to perform an upgrade on a node
#

ctx.logger.info("upgrade.py called: version={} url={}\n".format(inputs['version'],inputs['url']))

# check version, skip if supplied version is not greater than existing
version=ctx.instance.runtime_properties['app_version'] or 1.0

if(version < inputs['version']):
  ctx.logger.info("current version: {} : UPGRADING to {}".format(version,inputs['version']))

  # save rollback
  src_path=ctx.instance.runtime_properties['nodejs_source_path']
  ctx.logger.info("making backup: /bin/tar czf /tmp/rollback.tgz -C {} *".format(src_path))
  ret=subprocess.call("cd {};/bin/tar czf /tmp/rollback.tgz *".format(src_path),shell=True)

  # get new version
  newfile=urlparse(inputs['url']).path.split('/')[-1].encode('utf-8')
  ctx.logger.info("wget {} -O /tmp/{}".format(inputs['url'],newfile))
  ret=subprocess.call("/usr/bin/wget {} -O /tmp/{}".format(inputs['url'],newfile),shell=True)
  if(ret!=0):
    raise RecoverableError("download failed from url:{}".format(url))

  # replace existing with new
  ctx.logger.info("replacing app")
  ret=subprocess.call("cd {};rm *;tar xzf /tmp/{}".format(src_path,newfile),shell=True)
  if(ret!=0):
    raise RecoverableError("replacement with new version {} failed".format(newfile))

  # restart node
  pid=ctx.instance.runtime_properties['pid']
  proc=subprocess.Popen("ps -p {} -h|awk '{}'".format(pid,'{printf "%s %s",$5,$6}'),stdout=subprocess.PIPE,shell=True)
  if(proc.wait()!=0):
    raise RecoverableError("failed getting existing node process info")

  subprocess.call("kill {}".format(pid),shell=True)

  with open("/dev/null","w") as f:
    proc=subprocess.Popen(["nohup","{}/bin/node".format(ctx.instance.runtime_properties['nodejs_binaries_path']),"{}/server.js".format(ctx.instance.runtime_properties['nodejs_source_path'])],stdout=f, stderr=f, env={"NODEJS_PORT":str(ctx.node.properties['port'])})
    # store new pid
    ctx.instance.runtime_properties['pid']=proc.pid
    # update version
    old_version=ctx.instance.runtime_properties['app_version']
    ctx.instance.runtime_properties['app_version']=inputs['version']
    # save previous version for possible rollback
    ctx.instance.runtime_properties['app_prev_version']=old_version

else:
  ctx.logger.info("current version: {} : supplied version {}: NOT UPGRADING".format(version,inputs['version']))

