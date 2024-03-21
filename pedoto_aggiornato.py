import os
from itertools import islice
from collections import deque
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.cm as cm


def router(filepath):

    # associations = {
    #     "zebra": ["SCANNING -> DISCONNECTED", "COMPLETED -> DISCONNECTED"],
    #     "datalogic": ["COMPLETED -> DISCONNECTED"],
    #     "honey": ["COMPLETED -> DISCONNECTED"]
    # }

    endfile = os.path.basename(os.path.normpath(filepath))
    fileType = "zebra"

    if "datalogic" in endfile.lower() or "honey" in endfile.lower():
        fileType = "another"
        
    values = list()
    time_zero = ""
    with open(filepath, 'r') as file:
        # Read all lines
        lines = file.readlines()
        prev_lines = deque(maxlen=25)

        # All lines ..
        for index, (currentLine, nextLine) in enumerate(zip(lines, islice(lines, 1, None))):
            # Get check start time to calculate after difference between this value and event timestamp to generate plot
            if index == 0:
                time_zero = currentLine.split(" ")[1]

            # Event to append into events list
            element = dict()

            disconnectTimestamp = currentLine.split()[0] + " " + currentLine.split()[1]

            element["timestamp"] = disconnectTimestamp


            if "COMPLETED -> DISCONNECTED" in currentLine or (fileType == "zebra" and ("SCANNING -> DISCONNECTED" in currentLine or "ASSOCIATING -> DISCONNECTED" in currentLine)):
                element["INTRAROAMING"] = False
                # Set event type
                element["type"] = "DISCONNECT"
                print("DISCONNESSIONE: " + str(currentLine) + " at time: " + str(disconnectTimestamp))

                # Now get frequency value before disconnection ..
                for previous_line_index, previous_line in enumerate(reversed(list(prev_lines))):
                    if "Frequency: " in previous_line:
                        for substring in list(previous_line.split()):
                            if substring == "Frequency:":
                                substring_index = list(previous_line.split()).index(substring)
                                element["before"] = str(previous_line.split()[substring_index + 1])
                                print("Frequenza prima della disconnessione: " + str(previous_line.split()[substring_index + 1]))
                            if substring == "RSSI:":
                                substring_index = list(previous_line.split()).index(substring)
                                element["RSSI"] = str(previous_line.split()[substring_index + 1]).replace(",", "")
                                print("Valore RSSI prima della disconnessione: " + str(previous_line.split()[substring_index + 1]).replace(",", ""))
                        break

                # Now get frequency value after disconnection ..
                frequencyAfterDisconnect_isFound = False
                i = 1

                while not frequencyAfterDisconnect_isFound:
                    prox_line = lines[index + i]
                    if "Frequency: " in prox_line:
                        for substring_index, substring in enumerate(list(prox_line.split())):
                            if substring == "Frequency:":
                                element["after"] = str(prox_line.split()[substring_index + 1])
                                print("Frequenza dopo della disconnessione: " + str(prox_line.split()[substring_index + 1]))
                                frequencyAfterDisconnect_isFound = True
                                break
                    i = i + 1

                values.append(element)

            # Check if it changes internet connection
            elif "BSSID=" in currentLine:
                element["type"] = "ROAMING"

                # Get BSSID value
                elements = currentLine.split()
                bssIdFlag = elements[-1]
                bssIdValue = bssIdFlag.split("=")[1]
                print(bssIdValue)
                element["bssID"] = bssIdValue

                # Check if '4WAY_HANDSHAKE' or 'ROAMING' event type
                if "4WAY_HANDSHAKE" in nextLine:
                    print("BSSID value: " + str(bssIdValue) + " 4WAY_HANDSHAKE")
                    element["type"] = "4WAY_HANDSHAKE"

                # Now get frequency value before event ..
                for previous_line_index, previous_line in enumerate(reversed(list(prev_lines))):
                    if "Frequency: " in previous_line:
                        for substring in list(previous_line.split()):
                            if substring == "Frequency:":
                                substring_index = list(previous_line.split()).index(substring)
                                element["before"] = str(previous_line.split()[substring_index + 1])
                                print("Frequenza prima della disconnessione: " + str(previous_line.split()[substring_index + 1]))
                            if substring == "RSSI:":
                                substring_index = list(previous_line.split()).index(substring)
                                element["RSSI"] = str(previous_line.split()[substring_index + 1]).replace(",", "")
                                print("Valore RSSI prima della disconnessione: " + str(previous_line.split()[substring_index + 1]).replace(",", ""))
                            if substring == "BSSID:":
                                substring_index = list(previous_line.split()).index(substring)
                                prev_bssid = str(previous_line.split()[substring_index + 1]).replace(",", "")

                                if prev_bssid[:-2] == element["bssID"][:-2]:
                                    element["INTRAROAMING"] = True
                                else:
                                    element["INTRAROAMING"] = False
                        break

                # Now get frequency value before event ..
                frequencyAfterDisconnect_isFound = False
                i = 1

                while not frequencyAfterDisconnect_isFound:
                    prox_line = lines[index + i]
                    if "Frequency: " in prox_line:
                        for substring_index, substring in enumerate(list(prox_line.split())):
                            if substring == "Frequency:":
                                element["after"] = str(prox_line.split()[substring_index + 1])
                                print("Frequenza dopo della disconnessione: " + str(prox_line.split()[substring_index + 1]))
                                frequencyAfterDisconnect_isFound = True
                                break
                    i = i + 1

                values.append(element)

            # Get previous line to generate previous_lines array  ..
            prev_lines.append(currentLine)

    # Response
    result = {
        "values": values,
        "time_zero": datetime.strptime(time_zero, "%H:%M:%S.%f")
    }

    return result


if __name__ == '__main__':
    # /Users/automationnapoli/Downloads/wifi_zebra2.log
    # /Users/automationnapoli/Downloads/wifi_zebra_2.log
    # /Users/automationnapoli/Downloads/wifi_datalogic2.log
    # /Users/automationnapoli/Downloads/wifi_datalogic_triband.log
    path = 'wifi_datalogic.log'
    results = router(path)

    # Results generated
    eventList = results["values"]
    timeZero = results["time_zero"]

    # Values to insert into stem plot
    events = list()

    # X axis and Y axis
    x = list()
    y = list()

    # Stem colors
    colors = list()

    for event in eventList:
        # Get frequency value after and before single event
        event["before"] = event["before"].replace(",", "") if "," in event["before"] else event["before"]
        event["before"] = event["before"].replace("MHz", "") if "MHz" in event["before"] else event["before"]
        event["before"] = int(event["before"])

        event["after"] = event["after"].replace(",", "") if "," in event["after"] else event["after"]
        event["after"] = event["after"].replace("MHz", "") if "MHz" in event["after"] else event["after"]
        event["after"] = int(event["after"])

        # Get event time
        event["time"] = str(event["timestamp"]).split()[1]
        # Get timestamp
        timestamp = event["timestamp"].split(" ")[1]
        # Get event time as real timestamp with datetime library
        eventTime = datetime.strptime(timestamp, "%H:%M:%S.%f")

        # Calculating difference between check start time and current value to get x axis value to put value in the plot
        XaxisTimestamp = eventTime - timeZero
        # Get it as milliseconds
        XaxisTimestamp_To_milliseconds = XaxisTimestamp.seconds * 1000

        # Get Y axis value by event type
        YaxisValue = ""
        if event["type"] == "DISCONNECT":
            YaxisValue = -100
            colors.append('r')
        elif (event["type"] == "4WAY_HANDSHAKE" or event["type"] == "ROAMING") and event["INTRAROAMING"]:
            YaxisValue = int(event["RSSI"])
            colors.append('y')
        elif event["type"] == "ROAMING":
            YaxisValue = int(event["RSSI"])
            colors.append('b')
        elif event["type"] == "4WAY_HANDSHAKE":
            YaxisValue = int(event["RSSI"])
            colors.append('g')
        # Add new event ..
        events.append(
            {
                "type": event["type"],
                "XaxisTimestamp": int(XaxisTimestamp_To_milliseconds),
                "frequency_before": event["before"],
                "frequency_after": event["after"],
                "YaxisValue": int(YaxisValue),
                "label": str(timestamp),
                "bssID": str(event["bssID"]) if event["type"] != "DISCONNECT" else "",
                "logTimestamp": str(event["timestamp"]),
                "RSSI": str(event["RSSI"]),
                "INTRAROAMING": event["INTRAROAMING"]
            }
        )

        # Add X axis and Y axis value
        x.append(int(XaxisTimestamp_To_milliseconds))
        y.append(int(YaxisValue))

    # 10 e 5 sono valori espressi in pollici ...
    plt.figure(figsize=(20, 8))

    # Add all event as single event to add color ..
    for index, event_type in enumerate(events):
        color = 'r'
        if (event_type["type"] == "4WAY_HANDSHAKE" or event_type["type"] == "ROAMING") and event_type["INTRAROAMING"]:
            color = "y"
        elif event_type["type"] == "4WAY_HANDSHAKE":
            color = "g"
        elif event_type["type"] == "ROAMING":
            color = "b"
        plt.stem(x[index], y[index], color, markerfmt=color + "o")
        # plt.text(x[index], y[index], event_type["RSSI"], ha='center', va='bottom')

    # Generate colors legend to read file ..
    legends_elements = [
        Patch(facecolor='r', label='DISCONNECT'),
        Patch(facecolor='b', label='ROAMING'),
        Patch(facecolor='g', label='4WAY_HANDSHAKE'),
        Patch(facecolor='y', label='INTRAROAMING'),
    ]
    plt.legend(handles=legends_elements, loc="upper right", bbox_to_anchor=(1, 1))

    # Add all plot information
    plt.xlabel("Time in milliseconds")
    plt.ylabel("Y")
    plt.title("Grafico")
    plt.subplots_adjust(bottom=0.3)

    # Add timestamp label
    # A questo metodo puoi aggiungere il parametro fontsize per aumentare la grandezza dei timestamp ex. : fontsize=10 (mettilo in ultima posizione)
    plt.xticks(x, [ts["label"] for ts in events], rotation=270)

    # Save plot
    resultFolderPath = os.path.join(os.getcwd(), "results")

    # Generate result folder if not exists
    if not os.path.exists(resultFolderPath):
        os.makedirs(resultFolderPath)

    filename = "Test_" + str(datetime.now()).split(".")[0].replace(" ", "_").replace("-", "_").replace(":", "_") + "_" + path + ".jpeg"

    filepath = os.path.join(resultFolderPath, filename)
    plt.savefig(filepath, bbox_inches='tight', dpi=100)

    # Generate log
    minRange_6G = 5900
    maxRange_6G = 6600

    minRange_5G = 5170
    maxRange_5G = 5800

    minRange_2_4G = 2400
    maxRange_2_4G = 2600

    superString = ""

    disconnect_counter = 0
    roaming_counter = 0
    handshake_counter = 0
    intraroaming_counter = 0

    logFilename = os.path.join(resultFolderPath, "logFile_" + str(datetime.now()).split(".")[0].replace(" ", "_").replace("-", "_").replace(":", "_") + "_" + path + ".txt")
    logFilepath = os.path.join(resultFolderPath, logFilename)

    for singleEvent in events:
        # Frequency before event ..
        beforeConnectionType = "2.4GHz"

        if singleEvent["frequency_before"] > minRange_6G and singleEvent["frequency_before"] < maxRange_6G:
            beforeConnectionType = "6GHz"
        elif singleEvent["frequency_before"] > minRange_5G and singleEvent["frequency_before"] < maxRange_5G:
            beforeConnectionType = "5GHz"

        # Frequency after event ..
        afterConnectionType = "2.4GHz"

        if singleEvent["frequency_after"] > minRange_6G and singleEvent["frequency_after"] < maxRange_6G:
            afterConnectionType = "6GHz"
        elif singleEvent["frequency_after"] > minRange_5G and singleEvent["frequency_after"] < maxRange_5G:
            afterConnectionType = "5GHz"

        if str(singleEvent["type"]) == "DISCONNECT":
            disconnect_counter = disconnect_counter + 1
        elif str(singleEvent["type"]) == "ROAMING" and singleEvent["INTRAROAMING"]:
            intraroaming_counter = intraroaming_counter + 1
            roaming_counter = roaming_counter + 1
        elif str(singleEvent["type"]) == "4WAY_HANDSHAKE":
            handshake_counter = handshake_counter + 1
        elif str(singleEvent["type"]) == "ROAMING":
            roaming_counter = roaming_counter + 1

        intraroaming_info = ""

        if singleEvent["INTRAROAMING"]:
            intraroaming_info = "INTRAROAMING"

        if str(singleEvent["type"]) == "DISCONNECT":
            superString = superString + str(singleEvent["logTimestamp"]) + "  -  Event type: " + str(singleEvent["type"]) + "  -  Frequency before event: " + str(beforeConnectionType) + "  -  Frequency after event: " + str(afterConnectionType) + "  -  RSSI: " + str(singleEvent["RSSI"]) + ".\n"
        else:
            superString = superString + str(singleEvent["logTimestamp"]) + "  -  Event type: " + str(singleEvent["type"]) + "  -  BSSID value: " + str(singleEvent["bssID"]) + "  -  Frequency before event: " + str(beforeConnectionType) + "  -  Frequency after event: " + str(afterConnectionType) + "  -  RSSI: " + str(singleEvent["RSSI"]) + " - " + intraroaming_info + ".\n"

    superString = superString + "\n4WAY_HANDSHAKE: " + str(handshake_counter) + "  -  ROAMING: " + str(roaming_counter) + "  -  DISCONNECT: " + str(disconnect_counter) + "  -  INTRAROAMING: " + str(intraroaming_counter) + ".\n"

    # Generate Log file
    file = open(logFilepath, "w")
    file.write(str(superString))
    file.close()




