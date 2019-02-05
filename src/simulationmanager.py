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

    def getPlatoonByVehicle(self, v):
        return [p for p in self.getActivePlatoons() if v in p.getAllVehicles()]

    def getReleventPlatoon(self, vehicle):
        # Returns a single platoon that is most relevent to the given
        # vehicle by looking to see if the car in front is part of a platoon
        # It also checks that the platoon is heading in the right direction

        leadVeh = traci.vehicle.getLeader(vehicle, 20)
        if leadVeh:
            possiblePlatoon = self.getPlatoonByVehicle(leadVeh[0])
            assert(len(possiblePlatoon) <= 1,
                   "Only 1 platoon should be returned")
            if possiblePlatoon:
                if possiblePlatoon[0].checkVehiclePathsConverge([vehicle]):
                    return possiblePlatoon[0]

    def handleSimulationStep(self):
        # Handles a single step of the simulation
        # Update all active platoons in the scenario
        for platoon in self.getActivePlatoons():
            platoon.updatePlatoon()

        # See whether there are any vehicles that are not
        # in a platoon that should be in one
        vehiclesNotInPlatoons = [v for v in traci.vehicle.getIDList(
        ) if v not in self.getAllVehiclesInPlatoons()]

        for vehicleID in vehiclesNotInPlatoons:
            vehicleLane = traci.vehicle.getLaneID(vehicleID)
            # If we're not in a starting segment (speed starts as 0)
            if self.laneNodeConnections[vehicleLane] > 1:
                possiblePlatoon = self.getReleventPlatoon(vehicleID)
                if possiblePlatoon:
                    possiblePlatoon.addVehicleToPlatoon(vehicleID)
                else:
                    self.createPlatoon([vehicleID, ])
