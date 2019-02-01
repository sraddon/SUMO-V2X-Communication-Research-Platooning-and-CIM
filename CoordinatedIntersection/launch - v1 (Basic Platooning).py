from sumolib import checkBinary
sumoBinary = checkBinary("sumo-gui")

sumoCmd = [sumoBinary, "-c", "CoordIntersection.sumocfg", "--step-length", "0.1"]

import traci

traci.start(sumoCmd)
stoppedCarsByLane = dict()
step = 0
while step < 50000:
    idList = traci.vehicle.getIDList()
    processedLanes = set()
    for vehicleID in idList:
        vehicleSpeed = traci.vehicle.getSpeed(vehicleID)
        vehicleLane = traci.vehicle.getLaneID(vehicleID)

        if vehicleSpeed == 0:
            if vehicleLane in stoppedCarsByLane:
                stoppedCarsByLane[vehicleLane].add(vehicleID)
            else:
                stoppedCarsByLane[vehicleLane] = set([vehicleID,])
        else:
            for lane in stoppedCarsByLane.keys():
                if vehicleID in stoppedCarsByLane[lane]:
                    print(stoppedCarsByLane[lane])
                    for vehicle in stoppedCarsByLane[lane]:
                        if lane not in processedLanes:
                            if "Traffic" in lane:
                                #traci.vehicle.setSpeed(vehicle, traci.vehicle.getMaxSpeed(vehicle))
                                traci.vehicle.setTau(vehicle, 0)
                                traci.vehicle.setSpeedFactor(vehicle, 1)
                                traci.vehicle.setMinGap(vehicle, 1)
                                traci.vehicle.setImperfection(vehicle, 0)
                    processedLanes.add(lane)
                    stoppedCarsByLane[lane].remove(vehicleID)
    traci.simulationStep()
    step += 1

traci.close()