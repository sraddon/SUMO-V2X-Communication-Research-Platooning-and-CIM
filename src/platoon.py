import logging
import traci
import random


class Platoon():

    def __init__(self, startingVehicles):
        """Create a platoon, setting default values for all variables"""
        logging.info("Creating a new platoon with: %s", startingVehicles)
        self._active = True
        self._color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        self._leadVehicle = startingVehicles[0]  # must be better than this
        self._acceleration = traci.vehicle.getAcceleration(self._leadVehicle)
        self._currentSpeed = traci.vehicle.getSpeed(self._leadVehicle)
        self._lane = traci.vehicle.getLaneID(self._leadVehicle)
        self._lanePosition = traci.vehicle.getLanePosition(self._leadVehicle)
        self._maxSpeed = traci.vehicle.getMaxSpeed(self._leadVehicle)
        self._targetSpeed = -1
        self._vehicles = list(startingVehicles)
        traci.vehicle.setColor(self._leadVehicle, self._color)
        self.startBehaviour(startingVehicles[1:])

    def addVehicle(self, vehicle):
        """Adds a single vehicle to this platoon"""
        self._vehicles.append(vehicle)
        self.startBehaviour([vehicle, ])
        acceleration = traci.vehicle.getAcceleration(vehicle)
        maxSpeed = traci.vehicle.getMaxSpeed(vehicle)
        if maxSpeed < self._maxSpeed:
            self._maxSpeed = maxSpeed
        if acceleration < self._acceleration:
            self._acceleration = acceleration
        logging.info("Adding %s to platoon %s, New length: %s",
                     vehicle, self.getID(), len(self._vehicles))

    def checkVehiclePathsConverge(self, vehicles):
        # Check that the given vehicles are going to follow the lead
        # vehicle into the next edge
        leadVehicleRoute = self.getRemainingRouteOfVehicle(self._leadVehicle)
        if len(leadVehicleRoute) > 1:
            leadVehicleNextEdge = leadVehicleRoute[1]
            for vehicle in vehicles:
                if leadVehicleNextEdge not in traci.vehicle.getRoute(vehicle):
                    return False
        return True

    def disband(self):
        """Marks a platoon as dead and returns vehicles to normal"""
        self.stopBehvaviour()
        self._active = False
        logging.info("Disbanding platoon: %s", self.getID())

    def getAcceleration(self):
        return self._acceleration

    def getAllVehicles(self):
        """Retrieve the list of all the vehicles in this platoon"""
        return self._vehicles

    def getCurrentSpeed(self):
        return self._currentSpeed

    def getID(self):
        """Generates and returns a unique ID for this platoon"""
        return "%s" % (self._leadVehicle)

    def getLane(self):
        return self._lane

    def getLanesOfAllVehicles(self):
        return [traci.vehicle.getLaneID(v) for v in self.getAllVehicles()]

    def getLanePosition(self):
        return traci.lane.getLength(self._lane) - self._lanePosition

    def getLeadVehicle(self):
        return self._leadVehicle

    def getLength(self):
        """ Gets the total length of the platoon
            Done by taking the distance between the vehicle's front
            bumper and the end of the lane
            TODO: deal with vehicles being across two edges
        """
        laneLen = traci.lane.getLength(self._lane)
        front = laneLen - traci.vehicle.getLanePosition(self._leadVehicle)
        rear = laneLen - traci.vehicle.getLanePosition(self._vehicles[-1])
        rearVehicleLength = traci.vehicle.getLength(self._vehicles[-1]) * 2
        return rear - front + rearVehicleLength

    def getMaxSpeed(self):
        """ Gets the maximum speed of the platoon
        """
        return traci.vehicle.getMaxSpeed(self._leadVehicle)

    def getNumberOfVehicles(self):
        return len(self._vehicles)

    def getRemainingRouteOfVehicle(self, vehicle):
        vehicleRoute = traci.vehicle.getRoute(vehicle)
        return vehicleRoute[traci.vehicle.getRouteIndex(vehicle):]

    def getTargetSpeed(self):
        return self._targetSpeed

    def isActive(self):
        """Is the platoon currently active within the scenario"""
        return self._active

    def mergePlatoon(self, platoon):
        """Merges the given platoon into the current platoon"""
        if self.checkVehiclePathsConverge(platoon.getAllVehicles()) and platoon.getLane() == self.getLane():
            platoon.disband()
            for vehicle in platoon.getAllVehicles():
                self.addVehicle(vehicle)
            return True
        else:
            logging.error("Could not merge platoon %s with platoon %s",
                          platoon.getID(), self.getID())
            return False

    def removeTargetSpeed(self):
        """
        Removes the target speed from this platoon
        """
        self._targetSpeed = -1

    def setTargetSpeed(self, speed):
        self._targetSpeed = speed

    def startBehaviour(self, vehicles):
        """A function to start platooning a specific set of vehicles"""
        if self.isActive():
            for vehicle in vehicles:
                traci.vehicle.setColor(vehicle, self._color)
                traci.vehicle.setTau(vehicle, 0.05)
                traci.vehicle.setSpeedFactor(vehicle, 1)
                traci.vehicle.setMinGap(vehicle, 0)
                traci.vehicle.setImperfection(vehicle, 0)
        self.update()

    def stopBehvaviour(self):
        """Stops vehicles exhibiting platoon behaviour, if they are
        still present within the map"""
        vehicleList = traci.vehicle.getIDList()
        for vehicle in self._vehicles:
            if vehicle in vehicleList:
                traci.vehicle.setSpeed(vehicle, -1)
                traci.vehicle.setColor(vehicle, (255, 255, 255))
                traci.vehicle.setTau(vehicle, 1)
                traci.vehicle.setSpeedFactor(vehicle, 0.9)
                traci.vehicle.setImperfection(vehicle, 0.5)

    def update(self):
        """Performs updates to maintain the platoon
        1. set platoon location information using lead vehicle
        2. set the speed of all vehicles in the convoy,
           using the lead vehicle's current speed
        3. is this platoon still alive (in the map),
           should it be labelled as inactive?"""

        vehicleList = traci.vehicle.getIDList()
        # Is Active Update, if not disband and end update function
        if any([v not in vehicleList for v in self._vehicles]):
            self.disband()
            return None

        # Location Info Update
        self._lane = traci.vehicle.getLaneID(self._leadVehicle)
        self._lanePosition = traci.vehicle.getLanePosition(self._leadVehicle)

        # Speed Update
        self._currentSpeed = traci.vehicle.getSpeed(self._leadVehicle)
        if self._targetSpeed != -1:
            self._updateSpeed(self._targetSpeed)
        else:
            traci.vehicle.setSpeed(self._leadVehicle, -1)
            self._updateSpeed(self._currentSpeed, False)

        # Route updates
        # Check that all cars still want to continue onto the
        # next edge, otherwise disband the platoon
        if not self.checkVehiclePathsConverge(self.getAllVehicles()):
            self.disband()

    def _updateSpeed(self, speed, inclLeadingVeh=True):
        """ Sets the speed of all vehicles in the platoon
            If inclLeadingVeh set to false, then the leading vehicle is
            excluded from the speed change.
            Also checks that the platoon is bunched together, this allows
            for vehicles to "catch-up"
        """
        if inclLeadingVeh:
            traci.vehicle.setSpeed(self._leadVehicle, speed)

        # Non leading vehicles should follow the speed of the vehicle in front
        vehicles = self._vehicles[1:]
        for veh in vehicles:
            # If we're in range of the leader and they are moving
            # follow thier speed
            # Otherwise follow vehicle speed limit rules to catch up
            leadVeh = traci.vehicle.getLeader(veh, 20)
            if leadVeh and leadVeh[1] <= 10 and self._currentSpeed != 0:
                traci.vehicle.setSpeed(veh, speed)
            else:
                traci.vehicle.setSpeed(veh, -1)
