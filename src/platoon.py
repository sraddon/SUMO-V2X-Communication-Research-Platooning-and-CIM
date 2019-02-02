import logging
import traci


class Route():

    def __init__(self, vehicle):
        self.vehicle = vehicle
        self.route = traci.vehicle.getRoute(vehicle)
        self.destination = self.route[-1]

    def getRemainingRoute(self):
        return self.route[traci.vehicle.getRouteIndex(self.vehicle):]


class Platoon():

    def __init__(self, startingVehicles):
        # Create a platoon, setting default values for all variables
        logging.info("Creating a new platoon with: %s", startingVehicles)
        self._active = True
        self._leadVehicle = startingVehicles[0]  # must be better than this
        self._lane = traci.vehicle.getLaneID(self._leadVehicle)
        self._lanePosition = traci.vehicle.getLanePosition(self._leadVehicle)
        self._vehicles = set(startingVehicles)
        self._routes = [Route(v) for v in startingVehicles]
        self._platoonCutOff = None
        self.startPlatoonBehaviour()

    def addVehicleToPlatoon(self, vehicle):
        # Adds a single vehicle to this platoon
        self._vehicles.add(vehicle)
        self.startPlatoonBehaviour()
        self._routes.append(Route(vehicle))
        logging.info("Adding %s to platoon %s, New length: %s",
                     vehicle, self.getPlatoonID(), len(self._vehicles))

    def disbandPlatoon(self):
        # Marks a platoon as dead and returns vehicles to normal
        self.stopPlatoonBehvaviour()
        self._active = False

    def getAllVehicles(self):
        # Retrieve the list of all the vehicles in this platoon
        return self._vehicles

    def getPlatoonID(self):
        # Generates and returns a unique ID for this platoon
        return "%s" % (self._leadVehicle)

    def isActive(self):
        # Is the platoon currently active within the scenario
        return self._active

    def startPlatoonBehaviour(self):
        # A function to create a platoon of vehicles
        # out of a given list of vehicles
        if self._active:
            for vehicle in self._vehicles:
                traci.vehicle.setColor(vehicle, (255, 0, 0))
                traci.vehicle.setTau(vehicle, 0)
                traci.vehicle.setSpeedFactor(vehicle, 1)
                traci.vehicle.setMinGap(vehicle, 0)
                traci.vehicle.setImperfection(vehicle, 0)

    def stopPlatoonBehvaviour(self):
        # Stops vehicles exhibiting platoon behaviour, if they are
        # still present within the map
        vehicleList = traci.vehicle.getIDList()
        for vehicle in self._vehicles:
            if vehicle in vehicleList:
                traci.vehicle.setColor(vehicle, (255, 255, 255))
                traci.vehicle.setTau(vehicle, 1)
                traci.vehicle.setSpeedFactor(vehicle, 0.9)
                traci.vehicle.setMinGap(vehicle, 2.5)
                traci.vehicle.setImperfection(vehicle, 0.5)

    def updatePlatoon(self):
        # Performs updates to maintain the platoon
        # 1. set platoon location information using lead vehicle
        # 2. set the speed of all vehicles in the convoy,
        #    using the lead vehicle's current speed
        # 3. is this platoon still alive (in the map),
        #    should it be labelled as inactive?

        # Location Info Update
        vehicleList = traci.vehicle.getIDList()
        leadInMap = self._leadVehicle in vehicleList

        self._lane = traci.vehicle.getLaneID(
            self._leadVehicle) if leadInMap else None
        self._lanePosition = traci.vehicle.getLanePosition(
            self._leadVehicle) if leadInMap else None

        if leadInMap:
            # Speed Update
            self.updatePlatoonSpeed(traci.vehicle.getSpeed(self._leadVehicle))

            # Route updates
            for vehicle in self._vehicles:
                leadVehicleRoute = self._routes[0].getRemainingRoute()
                if len(leadVehicleRoute) > 1:
                    leadVehicleNextEdge = leadVehicleRoute[1]
                else:
                    break
                if leadVehicleNextEdge not in traci.vehicle.getRoute(vehicle):
                    self.disbandPlatoon()

        # Is Active Update
        if all([v not in vehicleList for v in self._vehicles]):
            logging.info("Setting platoon %s as inactive", self.getPlatoonID())
            self._active = False

    def updatePlatoonSpeed(self, speed):
        nonLeadingVehicles = self._vehicles - set([self._leadVehicle])
        for veh in nonLeadingVehicles:
            traci.vehicle.setSpeed(veh, speed if speed == 0 else speed + 10)
