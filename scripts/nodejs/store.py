from cloudify import ctx
from cloudify import exceptions
from cloudify.state import ctx_parameters as inputs
from cloudify.exceptions import RecoverableError,NonRecoverableError
from urlparse import urlparse

#
# Utility to perform an upgrade on a node
#

ctx.logger.info("store.py called: inputs={}\n".format(inputs))

version=ctx.instance.runtime_properties['app_version'] or 1.0

ctx.instance.runtime_properties[inputs['property']]=version

ctx.instance.update()

ctx.logger.info("store.py done")
