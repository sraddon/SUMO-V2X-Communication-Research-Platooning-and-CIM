import traci
from sumolib import checkBinary
import logging


class Platoon():

    def __init__(self, startingVehicles):
        # Create a platoon, setting default values for all variables
        logging.info("Creating a new platoon with: %s", startingVehicles)
        self._active = True
        self._leadVehicle = startingVehicles[0]  # must be better than this
        self._lane = traci.vehicle.getLaneID(self._leadVehicle)
        self._lanePosition = traci.vehicle.getLanePosition(self._leadVehicle)
        self._vehicles = set(startingVehicles)
        self.startPlatoonBehaviour()

    def addVehicleToPlatoon(self, vehicle):
        # Adds a single vehicle to this platoon
        self._vehicles.add(vehicle)
        self.startPlatoonBehaviour()
        logging.info("Adding %s to platoon %s, New length: %s", vehicle, self.getPlatoonID(), len(self._vehicles))

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
                traci.vehicle.setTau(vehicle, 1)
                traci.vehicle.setSpeedFactor(vehicle, 0.9)
                traci.vehicle.setMinGap(vehicle, 2.5)
                traci.vehicle.setImperfection(vehicle, 0.5)

    def updatePlatoon(self):
        # Performs updates to maintain the platoon
        # 1. set platoon location information using lead vehicle
        # 2. is this platoon still alive (in the map),
        #    should it be labelled as inactive?

        vehicleList = traci.vehicle.getIDList()
        leadInMap = self._leadVehicle in vehicleList

        self._lane = traci.vehicle.getLaneID(
            self._leadVehicle) if leadInMap else None

        self._lanePosition = traci.vehicle.getLanePosition(
            self._leadVehicle) if leadInMap else None

        if all([v not in vehicleList for v in self._vehicles]):
            logging.info("Setting platoon %s as inactive", self.getPlatoonID())
            self._active = False


class SimulationManager():

    def __init__(self):
        self.platoons = list()
        # Generate all node link numbers at first run,
        # this markedly improves performance
        self.laneNodeConnections = dict()
        for lane in traci.lane.getIDList():
            self.laneNodeConnections[lane] = traci.lane.getLinkNumber(lane)

    def createPlatoon(self, vehicles):
        # Creates a platoon with the given vehicles
        platoon = Platoon(vehicles)
        self.platoons.append(platoon)

    def getActivePlatoons(self):
        # Gets all active platoons
        return [p for p in self.platoons if p.isActive()]

    def getAllVehiclesInPlatoons(self):
        # Gets all vehicles in every active platoon
        return flatten(p.getAllVehicles() for p in self.getActivePlatoons())

    def getPlatoonByLane(self, lane):
        # Gets platoons corresponding to a given lane
        return [p for p in self.getActivePlatoons() if lane == p._lane]

    def getReleventPlatoon(self, vehicle):
        # Returns a single platoon that is most relevent to the given
        # vehicle
        # 1. Is there a platoon in the current lane?
        # 2. Which one is the closest in front?
        # None will be returned if no platoon is found that is relevent
        #
        # TODO: Make is so that a platoon is only relevent if it
        # is directly in front of the vehicle

        def posSort(val):
            # Sorting key function sort platoons by position in the lane
            return val._lanePosition

        lane = traci.vehicle.getLaneID(vehicle)
        lanePosition = traci.vehicle.getLanePosition(vehicle)
        possiblePlatoons = self.getPlatoonByLane(lane)
        if len(possiblePlatoons) == 1:
            return possiblePlatoons[0]
        else:
            possiblePlatoons.sort(key=posSort)
            currBestPlatoon = None
            for p in possiblePlatoons:
                if p._lanePosition > lanePosition:
                    break
                currBestPlatoon = p
        return currBestPlatoon

    def handleSimulationStep(self):
        # Handles a single step of the simulation
        # Update all active platoons in the scenario
        for platoon in self.getActivePlatoons():
            platoon.updatePlatoon()

        # See whether there are any vehicles that are not
        # in a platoon that should be in one
        vehiclesNotInPlatoons = [v for v in traci.vehicle.getIDList() if v not in self.getAllVehiclesInPlatoons()]
        for vehicleID in vehiclesNotInPlatoons:
            vehicleSpeed = traci.vehicle.getSpeed(vehicleID)
            vehicleLane = traci.vehicle.getLaneID(vehicleID)
            # If we're not in a starting segment (speed starts as 0)
            if self.laneNodeConnections[vehicleLane] > 1 and vehicleSpeed == 0:
                possiblePlatoon = self.getReleventPlatoon(vehicleID)
                if possiblePlatoon:
                    possiblePlatoon.addVehicleToPlatoon(vehicleID)
                else:
                    self.createPlatoon([vehicleID, ])


def flatten(l):
    # A basic function to flatten a list
    return [item for sublist in l for item in sublist]


# Check SUMO has been set up properly
sumoBinary = checkBinary("sumo-gui")

# Set up logger
logging.basicConfig(format='%(asctime)s %(message)s')
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Start Simulation and step through
traci.start([sumoBinary, "-c", "CoordIntersection.sumocfg",
             "--step-length", "0.1"])
step = 0
manager = SimulationManager()
while step < 5000:
    manager.handleSimulationStep()
    traci.simulationStep()
    step += 1

traci.close()
