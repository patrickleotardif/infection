import random
from collections import *

#Note that for easier names, 'parents' & 'children' will be used
#instead of 'coached_by' & 'users_coached'

class User:
  def __init__(self,uid,parents=set(),children=set(),version=0):
    self.uid = uid
    self.version = version
    self.parents = parents
    self.children = children
    self.links = parents | children
  def addParents(self,new_parents):
    self.parents = set(new_parents) | self.parents
    self.links = self.parents | self.children
  def addChildren(self,new_children):
    self.children = set(new_children) | self.children
    self.links = self.parents | self.children

#The following represents a template to create random graphs of users
#It follows a logic of defining layers of hierarchies
#e.g. layer 1 are users with no children,
#     layer 2 are users with children from layer 1, etc.
#For each layer, there are two main datapoints, 'pct' and 'dist'
# 'pct' : Percentage of total graph that is encompassed in layer
# 'dist': Describes distribution of how many parents each element has
# fields: {'min': min value of cdf, 'cdf': cumulative distribution func.}
# You can infer the pdf as in (min: 1, cdf:[0.5,1]) -> pdf : {1:0.5, 2:0.5}
#
#TODO add tests to make sure percentages add up and template conforms to spec
#TODO add different template views if you have other statistics you want to
#create a graph based on (e.g. average number of children instead of parents)
graphTemplates = [ 
  {
    1:  {'pct': .8, 'dist': {'min':1,'cdf':[.7,.9,1]} },
    2:  {'pct': .12,'dist': {'min':0,'cdf':[.7,.85,1]} },
    3:  {'pct': .08 },
  }
]

#Input {1: {'size': %pop}, 2: {'size': %pop}, ...}  and size = int
#Output { 1: [uids in layer], 2: [uids in layer], ...}
#
#Trivial example {1: {'size': 0.7}, 2: {'size': 0.3}} and size = 10
#Output is { 1: [0,1,2,3,4,5,6], 2: [7,8,9] }
def usersByLayerFromTemplate(template,size):
  layers = {}
  min = 0
  max = 0 
  for k,v in template.iteritems():
    max += int(v['pct']*size)
    layers[k] = range(min,max)
    min = max
  return layers

#Given a dist as defined in graphTemplates return random value
#representing number of parents for the element
def getRandomNumParents(dist):
  r = random.random()
  numParents = dist['min']
  for val in dist['cdf']:
    if val >= r:
      return numParents
    else:
      numParents += 1

#Based on a given graph template, return a random dictionary of users
#(i.e. users[user id] returns a User object)
#
#Note: This method can cause higher level layer Users to be
#entirely unconnected (i.e. nobody in layer 2 ends up connecting to layer 3)
#Possible TODO to enforce connectedness of graph
def randomHierarchicalGraph(size=10000,template=graphTemplates[0]):
  usersByLayer = usersByLayerFromTemplate(template,size)
  users = {k: User(k) for k in range(size)}
  
  for layer,usersInLayer in usersByLayer.iteritems(): 
    if 'dist' not in template[layer]: 
      break #don't process the last layer, it has no parents
    for uid in usersInLayer:
      numParents = getRandomNumParents(template[layer]['dist'])
      newParents = random.sample(usersByLayer[layer+1],numParents) 
      users[uid].addParents(newParents)
      for newParent in newParents:
        users[newParent].addChildren([uid])
  return users

#Given dictionary of Users and a seed, infect all connected Users
#[returns a set of uids (user ids) that are infected]
def totalInfection(users,seed):
  queue = deque([seed])
  infected = set([seed])

  while(len(queue) > 0):
    uid = queue.pop()
    infected.add(uid)
    queue.extend(users[uid].links - infected)

  return infected

#higher score = more links where parents and children are different
def calculateBadness(user,infected):
  return len(user.links - infected) - len(user.links & infected)

#Given dictionary of Users, a seed, and min/max threshold, return
#a good set of users to infect that minimizes badness
#[returns a set of uids (user ids) that are infected]
def limitedInfection(users,seed,minUsers,maxUsers):
  queue = [] 
  queue.append((0,seed))
  infected = set()
  totalBadness = 0 #see below explanation on this variable
  temporaryInfected = set() #see below explanation on this variable

  while(len(infected) < maxUsers) : 
    badness, uid = sorted(queue)[0] #current least bad option
    queue.remove((badness,uid))
    infected.add(uid)
    existingQueueItems = set([x[1] for x in queue])
    queue = [] #emptying queue since we need to recompute badnesses

    #We need to recompute badness of the existingQueueItems since infected set
    #is different now that we've added another node
    nodesToAdd = (users[uid].links | existingQueueItems) - infected

    #case where fully connected graph is already achieved 
    if len(nodesToAdd) == 0:
     break

    for linkedNode in nodesToAdd:
      queue.append( (calculateBadness(users[linkedNode],infected), linkedNode))

    #once we've exceeded the minimum threshold, we should only be adding nodes
    #where the additions reduce the badness of the existing graph
    #totalBadness measures this while temporaryInfected keeps track of nodes
    #that we aren't yet sure should be added to the final set
    if len(infected) >  minUsers:
      totalBadness += badness
      if totalBadness >= 0:
        temporaryInfected.add(uid)
      else: #if we come across a reduction in badness, reset
        temporaryInfected = set()
        totalBadness = 0

  return infected - temporaryInfected

#TODO option parsers to allow different combinations of parameters to be used
def test():
  users = randomHierarchicalGraph(size=10000)
  seed = 42 #because
  totalInfected_user_count = len(totalInfection(users,seed))
  limitedInfected_user_count = len(limitedInfection(users,seed,300,500))

  print('''
    Generated random graph of 10K users
    Total infection of user %s yielded %s users infected
    Limited infection ([300,500] users) of user 42 yielded %s users infected
  ''' % (seed,totalInfected_user_count,limitedInfected_user_count))        

if __name__ == "__main__":
    test()




