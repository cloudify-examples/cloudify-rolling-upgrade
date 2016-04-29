#
# Rolling upgrade workflow.  Process nodes one by one.
#
import time
import sys
import traceback
from cloudify.workflows import ctx
from cloudify.workflows import parameters as p

# get list of target node instances
# limit<0 means get all
def get_targets(limit=-1):
  targets=[]
  count=0
  if(limit==-1):
    limit=10000000
  
  for node in ctx.nodes:
    if("webapp_upgrade.rollback" in node.operations):
      for instance in node.instances:
        targets.append(instance)
  return targets

# Either upgrades or rolls back
# 
# rollback: boolean 
# instances: instances to process
def process_instances(instances,rollback):

  if(not rollback):
    ctx.logger.info("upgrading")
  else:
    ctx.logger.info("rolling back")

  ctx.logger.info("candidate instance cnt={}".format(len(instances)))

  if("percentage" in p):
    if(len(instances)>0):
      count=int(len(instances)*float(p['percentage'])/100.)
      if(count==0):
        ctx.logger.warning("upgrade percentage yields no target instances")
        return
      else:
        ctx.logger.info("upgrading {} out of {} instances\n".format(count,len(instances)))
        for i in range(len(instances)-count):
          instances.pop()
     
  # for each node implementing "upgradable_webapp"
  for instance in instances:
    # Unregister from load balancer
    for rel in instance.relationships:
      if(rel.relationship.is_derived_from(p['lb_interface'])):
        ctx.logger.info("unlinking {}\n".format(instance.id))
        ret=rel.execute_target_operation("cloudify.interfaces.relationship_lifecycle.unlink")
        break
      
    if(not rollback): 
      # Upgrade webapp
      instance.execute_operation("webapp_upgrade.upgrade",kwargs={"version":p["version"],"url":p["url"]})
    else:
      # Rollback webapp
      instance.execute_operation("webapp_upgrade.rollback")

    # Re-register with load balancer
    for rel in instance.relationships:
      if(rel.relationship.is_derived_from(p['lb_interface'])):
        ctx.logger.info("establishing {}\n".format(instance.id))
        rel.execute_target_operation("cloudify.interfaces.relationship_lifecycle.establish")
        break
    
    if(p['pause']):
      time.sleep(p['pause'])


def upgrade():
  instances=get_targets()

  try:
    process_instances(instances,False)
  except NameError as ex:
    ctx.logger.error("caught exception: {}\n".format(ex))
    process_instances(instances,True)
    

upgrade()
