# featureExtractors.py
# --------------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).
from __future__ import division

"Feature extractors for Pacman game states"

from game import Actions, Directions, Grid
import util
import random

class FeatureExtractor:
    def getFeatures(self, state, action):
        """
          Returns a dict from features to counts
          Usually, the count will just be 1.0 for
          indicator functions.
        """
        util.raiseNotDefined()

class IdentityExtractor(FeatureExtractor):
    def getFeatures(self, state, action):
        feats = util.Counter()
        feats[(state,action)] = 1.0
        return feats

class CoordinateExtractor(FeatureExtractor):
    def getFeatures(self, state, action):
        feats = util.Counter()
        feats[state] = 1.0
        feats['x=%d' % state[0]] = 1.0
        feats['y=%d' % state[0]] = 1.0
        feats['action=%s' % action] = 1.0
        return feats

def closestFood(pos, food, walls):
    """
    closestFood -- this is similar to the function that we have
    worked on in the search project; here its all in one place
    """
    fringe = [(pos[0], pos[1], 0)]
    expanded = set()
    while fringe:
        pos_x, pos_y, dist = fringe.pop(0)
        if (pos_x, pos_y) in expanded:
            continue
        expanded.add((pos_x, pos_y))
        # if we find a food at this location then exit
        if food[pos_x][pos_y]:
            return dist
        # otherwise spread out from the location to its neighbours
        nbrs = Actions.getLegalNeighbors((pos_x, pos_y), walls)
        for nbr_x, nbr_y in nbrs:
            fringe.append((nbr_x, nbr_y, dist+1))
    # no food found
    return None

class SimpleExtractor(FeatureExtractor):
    """
    Returns simple features for a basic reflex Pacman:
    - whether food will be eaten
    - how far away the next food is
    - whether a ghost collision is imminent
    - whether a ghost is one step away
    """

    def getFeatures(self, state, action):
        # extract the grid of food and wall locations and get the ghost locations
        food = state.getFood()
        walls = state.getWalls()
        ghosts = state.getGhostPositions()
        features = util.Counter()

        features["bias"] = 1.0
        # compute the location of pacman after he takes the action
        x, y = state.getPacmanPosition()
        dx, dy = Actions.directionToVector(action)
        next_x, next_y = int(x + dx), int(y + dy)

        # count the number of ghosts 1-step away
        features["#-of-ghosts-1-step-away"] = sum((next_x, next_y) in Actions.getLegalNeighbors(g, walls) for g in ghosts)

        # if there is no danger of ghosts then add the food feature
        if not features["#-of-ghosts-1-step-away"] and food[next_x][next_y]:
            features["eats-food"] = 1.0

        dist = closestFood((next_x, next_y), food, walls)
        if dist is not None:
            # make the distance a number less than one otherwise the update
            # will diverge wildly
            features["closest-food"] = float(dist) / (walls.width * walls.height)
        features.divideAll(10.0)
        return features

class NewExtractor(FeatureExtractor):
    def __init__(self):
        self.visited = None
    """
    Design you own feature extractor here. You may define other helper functions you find necessary.
    """
    def getFeatures(self, state, action):
        "*** YOUR CODE HERE ***"
        """
        Returns simple features for a basic reflex Pacman:
        - whether food will be eaten
        - how far away the next food is
        - whether a ghost collision is imminent
        - whether a ghost is one step away
        """
        # extract the grid of food and wall locations and get the ghost locations
        food = state.getFood()
        walls = state.getWalls()
        ghosts = state.getGhostPositions()
        features = util.Counter()
        capsules = state.getCapsules()
        ghostsStates = state.getGhostStates()

        features["bias"] = 1.0
        
        if self.visited is None:
            self.visited = Grid(walls.width, walls.height, False)

        # compute the location of pacman after he takes the action
        x, y = state.getPacmanPosition()
        dx, dy = Actions.directionToVector(action)
        next_x, next_y = int(x + dx), int(y + dy)

        # count the number of ghosts 1-step away
        #print(str(state.getGhostStates()[0].configuration.getPosition()) + ";" + str(state.getGhostStates()[0].scaredTimer))
        
        ghostsPosThatAreNotScared = []
        ghostsPosThatAreScared = []

        for i in range(len(ghosts)):
            isScared = state.getGhostStates()[i].scaredTimer > 0
            if isScared:
                # If this ghost is scared, add the (x,y) position to the scared list
                ghostsPosThatAreScared.append(ghosts[i])
            else:
                # Else, add the (x,y) position to the not scared list
                ghostsPosThatAreNotScared.append(ghosts[i])

        # Only consider ghosts that are not scared
        features["#-of-ghosts-1-step-away"] = sum((next_x, next_y) in Actions.getLegalNeighbors(g, walls) for g in ghostsPosThatAreNotScared)

        ateSomethingGood = False
        # if there is no danger of ghosts then add the food feature
        if not features["#-of-ghosts-1-step-away"] and food[next_x][next_y]:
            features["eats-food"] = 1.0
            ateSomethingGood = True

        # if there is no danger of ghosts then add the capsule feature
        if not features["#-of-ghosts-1-step-away"] and (next_x, next_y) in capsules:
            features["eats-capsules"] = 5.0
            ateSomethingGood = True

        # if the pacman eats a scared ghost
        if (next_x, next_y) in ghostsPosThatAreScared:
            features["eats-scaared-ghost"] = 5.0
            ateSomethingGood = True
        
        # # if the pacman did not eat anything good
        # if not ateSomethingGood:
        #     features["not-eat-anything"] = 1.0

        # if the pacman did not move
        features["not-move"] = 0.0
        if (x == next_x) and (y == next_y):
            features["not-move"] = 1.0

        # features["hit-wall"] = 0.0
        # if x + 1 == next_x and walls[next_x + 1][next_y]:
        #     features["hit-wall"] = 1.0
        # if x - 1 == next_x and walls[next_x - 1][next_y]:
        #     features["hit-wall"] = 1.0
        # if y + 1 == next_y and walls[next_x][next_y + 1]:
        #     features["hit-wall"] = 1.0
        # if y - 1 == next_y and walls[next_x][next_y - 1]:
        #     features["hit-wall"] = 1.0

        manhattan_distance = []
        for f in food.asList():
            manhattan_distance.append((abs(f[0] - next_x) + abs(f[1] - next_y)) )
        features["num-of-food"] = len(food.asList()) /1.5
        features["total-manhattan-distance"] = (10) * sum(manhattan_distance) / (walls.width * walls.height * (walls.width + walls.height))

        features["revisit-old-nodes"] = 0.0
        if self.visited[next_x][next_y]:
             features["revisit-old-nodes"] = 10.0

        self.visited[x][y] = True


        dist = closestFood((next_x, next_y), food, walls)
        if dist is not None:
            # make the distance a number less than one otherwise the update
            # will diverge wildly
            features["closest-food"] = float(dist) / (walls.width * walls.height)
        features.divideAll(10.0)
        return features


        
