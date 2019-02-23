import traci
import logging


class IntersectionController():

    def __init__(self, intersection, zip=True):
        self.name = intersection
        self.zip = zip
        lanes = traci.trafficlights.getControlledLanes(intersection)
        self.lanesServed = set(lanes)
        self.platoons = []

    def addPlatoon(self, platoon):
        self.platoons.append(platoon)

    def _getPlatoonLanePosition(self, platoon):
        if platoon.getLane() in self.lanesServed:
            return platoon.getLanePosition()
        return 0

    def findAndAddReleventPlatoons(self, platoons):
        def platoonPosition(platoon):
            return self._getPlatoonLanePosition(platoon)

        platoons.sort(key=platoonPosition)
        for p in platoons:
            if p.getLane() in self.lanesServed and p not in self.platoons:
                self.addPlatoon(p)

    def removePlatoon(self, platoon):
        self.platoons.remove(platoon)
        # Resume normal speed behaviour
        platoon.removeTargetSpeed()
        for v in platoon.getAllVehicles():
            traci.vehicle.setSpeedMode(v, 31)

    def updatePlatoonSpeed(self, platoon, reservedTime):
        distanceToTravel = self._getPlatoonLanePosition(platoon)
        platoonCurrentSpeed = platoon.getCurrentSpeed()
        if distanceToTravel > 20:
            speed = distanceToTravel / (reservedTime or 1)
            speed = max([speed, platoon.getAcceleration()])
            # If we're above the max speed, we use that instead
            if speed >= platoonCurrentSpeed:
                platoon.removeTargetSpeed()
            else:
                platoon.setTargetSpeed(speed)
        else:
            platoon.setTargetSpeed(platoon.getCurrentSpeed())

        if reservedTime == 0:
            lenThruJunc = self._getPlatoonLanePosition(platoon) + platoon.getLength()
        else:
            lenThruJunc = platoon.getLength()

        if platoon.getLane() in self.lanesServed:
            return 0.2 + reservedTime + (lenThruJunc / (platoonCurrentSpeed or 1))
        return 0

    def update(self):
        """
        Updates the intersection
        """
        reservedTime = 0
        for p in self.platoons:
            for v in p.getAllVehicles():
                traci.vehicle.setSpeedMode(v, 0)
            # Do we need to remove any platoons from our control?
            if all([l not in self.lanesServed for l in p.getLanesOfAllVehicles()]):
                self.removePlatoon(p)
            # Update the speeds of the platoon
            else:
                reservedTime = self.updatePlatoonSpeed(p, reservedTime)
        self.logIntersectionStatus(reservedTime)

    def logIntersectionStatus(self, reservation=None):
        if self.platoons:
            logging.info("------------%s Information------------", self.name)
            for p in self.platoons:
                logging.info("Platoon: %s, Target: %s, Current: %s ", p.getID(), p.getTargetSpeed(), p.getCurrentSpeed())
            if reservation:
                logging.info("Total time reserved: %s", reservation)