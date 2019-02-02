from src.platoon import Platoon
from src.simlib import flatten
import traci


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
