from src.intersectionController import IntersectionController
from src.platoon import Platoon
from src.vehicle import Vehicle
from src.simlib import flatten


import traci

class SimulationManager():

    def __init__(self, pCreation=True, iCoordination=True, iZipping=True):
        self.intersections = []
        self.platoons = list()
        self.platoonCreation = pCreation
        self.vehicles = list()
        if iCoordination:
            for intersection in traci.trafficlights.getIDList():
                controller = IntersectionController(intersection, iZipping)
                self.intersections.append(controller)

    def createPlatoon(self, vehicles):
        # Creates a platoon with the given vehicles
        platoon = Platoon(vehicles)
        self.platoons.append(platoon)

    def getActivePlatoons(self):
        # Gets all active platoons
        return [p for p in self.platoons if p.isActive()]

    def getAllVehiclesInPlatoons(self):
        # Gets all vehicles in every active platoon
        return flatten(p.getAllVehiclesByName() for p in self.getActivePlatoons())

    def getPlatoonByLane(self, lane):
        # Gets platoons corresponding to a given lane
        return [p for p in self.getActivePlatoons() if lane == p.getLane()]

    def getPlatoonByVehicle(self, v):
        return [p for p in self.getActivePlatoons() if v in p.getAllVehiclesByName()]

    def getReleventPlatoon(self, vehicle):
        # Returns a single platoon that is most relevent to the given
        # vehicle by looking to see if the car in front is part of a platoon
        # It also checks that the platoon is heading in the right direction
        leadVeh = vehicle.getLeader()
        if leadVeh and leadVeh[1] < 10:
            possiblePlatoon = self.getPlatoonByVehicle(leadVeh[0])
            assert(len(possiblePlatoon) <= 1,
                   "Only 1 platoon should be returned")
            if possiblePlatoon:
                if possiblePlatoon[0].checkVehiclePathsConverge([vehicle]) and vehicle not in possiblePlatoon[0].getAllVehicles():
                    return possiblePlatoon[0]

    def handleSimulationStep(self):
        allVehicles = traci.vehicle.getIDList()
        # Check mark vehicles as in-active if they are outside the map
        for v in self.vehicles:
            if v.getName() not in allVehicles:
                v.setInActive()

        if self.intersections:
            for inControl in self.intersections:
                inControl.findAndAddReleventPlatoons(self.getActivePlatoons())
                inControl.update()

        if self.platoonCreation:
            # Handles a single step of the simulation
            # Update all active platoons in the scenario
            for platoon in self.getActivePlatoons():
                platoon.update()
                if platoon.canMerge():
                    lead = platoon.getLeadVehicle().getLeader()
                    if lead:
                        leadPlatoon = self.getPlatoonByVehicle(lead[0])
                        if leadPlatoon:
                            leadPlatoon[0].mergePlatoon(platoon)
            
            # See whether there are any vehicles that are not
            # in a platoon that should be in one
            vehiclesNotInPlatoons = [v for v in allVehicles if v not in self.getAllVehiclesInPlatoons()]

            for vehicleID in vehiclesNotInPlatoons:
                vehicle = Vehicle(vehicleID)
                self.vehicles.append(vehicle)
                vehicleLane = vehicle.getLane()
                # If we're not in a starting segment (speed starts as 0)
                possiblePlatoon = self.getReleventPlatoon(vehicle)
                if possiblePlatoon:
                    possiblePlatoon.addVehicle(vehicle)
                else:
                    self.createPlatoon([vehicle, ])
