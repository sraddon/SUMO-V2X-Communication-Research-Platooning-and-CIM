import traci

class Vehicle():
    
    def __init__(self, vehicle):
        self._active = True
        self._acceleration = traci.vehicle.getAcceleration(vehicle)
        self._length = traci.vehicle.getLength(vehicle)
        self._maxSpeed = traci.vehicle.getMaxSpeed(vehicle)
        self._name = vehicle
        self._route = traci.vehicle.getRoute(vehicle)
        self._previouslySetValues = dict()
        self._speedMode = traci.vehicle.getSpeedMode(vehicle)

    def getAcceleration(self):
        return self._acceleration

    def isActive(self):
        return self._active

    def getLane(self):
        return traci.vehicle.getLaneID(self.getName())

    def getLanePosition(self):
        return traci.vehicle.getLanePosition(self.getName())

    def getLanePositionFromFront(self):
        return traci.lane.getLength(self.getLane()) - self.getLanePosition()

    def getLeader(self):
        return traci.vehicle.getLeader(self.getName(), 20)

    def getLength(self):
        return self._length

    def getMaxSpeed(self):
        return self._maxSpeed

    def getName(self):
        return self._name

    def getRemainingRoute(self):
        return self._route[traci.vehicle.getRouteIndex(self.getName()):]

    def getSpeed(self):
        return traci.vehicle.getSpeed(self.getName())

    def setColor(self, color):
        self._setAttr("setColor", color)

    def setInActive(self):
        self._active = False

    def setImperfection(self, imperfection):
        self._setAttr("setImperfection", imperfection)

    def setMinGap(self, minGap):
        self._setAttr("setMinGap", minGap)

    def setTau(self, tau):
        self._setAttr("setTau", tau)

    def setSpeed(self, speed):
        self._setAttr("setSpeed", speed)

    def setSpeedMode(self, speedMode):
        self._setAttr("setSpeedMode", speedMode)

    def setSpeedFactor(self, speedFactor):
        self._setAttr("setSpeedFactor", speedFactor)

    def _setAttr(self, attr, arg):
        if self.isActive():
            if attr in self._previouslySetValues:
                if self._previouslySetValues[attr] == arg:
                    return
            self._previouslySetValues[attr] = arg
            getattr(traci.vehicle, attr)(self.getName(), arg)