import datetime
import time
import json
import copy

__functioncontrolfolder = {
    "name":"control","type":"folder","children":[
        {"name":"status","type":"variable","value":"idle"},                 # one of ["finished","running"]
        {"name":"progress","type":"variable","value":0},                    # a value between 0 and 1 ( for showing progress in the ui
        {"name":"result","type":"variable","value":"ok"},                   # of ["ok","error","pending" or a last error message]
        {"name":"signal","type":"variable","value":"nosignal"},             # of ["nosignal","interrupt"]
        {"name":"executionCounter","type":"variable","value":0},            # a counter which is increased on each execution of this function
        {"name":"lastExecutionDuration", "type": "variable", "value": 0},   #in float seconds
        {"name":"lastStartTime","type":"variable","value":"not yet"},       # in isoforma-string
        {"name":"executionCounter","type":"variable","value":0},            # increases on each SUCESSFUL completion
        {"name":"executionType","type":"const","value":"async"}             # one of ["sync", "async"] sync: is executed on the main server thread, async: in separate thread
    ]
}





periodicTimer = {
    "name":"periodicTimer",
    "type":"function",
    "functionPointer":"system.periodic_timer",   #filename.functionname
    "autoReload":False,                                 #set this to true to reload the module on each execution
    "children":[
        {"name":"target","type":"referencer"},
        {"name":"periodSeconds","type":"const","value":1},
        {"name":"description","type":"const","value":"periodic timer"},
        {"name":"lastTimeout","type":"variable","value":"not yet"},
        {"name":"lastDuration","type":"variable","value":"not yet"},
        {"name":"executionCounter","type":"variable","value":0},
        __functioncontrolfolder,
    ]
}

counter = {
    "name":"counter",
    "type":"function",
    "functionPointer":"system.counter_f",   #filename.functionname
    "autoReload":False,                                 #set this to true to reload the module on each execution
    "children":[
        {"name":"counter","type":"variable"},
        __functioncontrolfolder,
    ]
}


observer = {
    "name":"observer",
    "type":"observer",
    "children":[
        {"name": "enabled", "type": "const", "value": False},           # turn on/off the observer
        {"name": "triggerCounter","type":"variable","value":0},         #  increased on each trigger
        {"name": "lastTriggerTime","type":"variable","value":""},       #  last datetime when it was triggered
        {"name": "targets","type":"referencer"},                        #  pointing to the nodes observed
        {"name": "properties","type":"const","value":["value"]},        #  properties to observe [“children”,“value”, “forwardRefs”]
        {"name": "onTriggerFunction","type":"referencer"},              #  the function(s) to be called when triggering
        {"name": "triggerSourceId","type":"variable"},                  #  the sourceId of the node which caused the observer to trigger
        {"name": "hasEvent","type":"const","value":False},              # set to event string iftrue if we want an event as well
        {"name": "eventString","type":"const","value":"observerdefaultevent"},              # the string of the event
        {"name": "eventData","type":"const","value":{"text":"observer status update"}}      # the value-dict will be part of the SSE event["data"] , the key "text": , this will appear on the page,
    ]
}








def counter_f(functionNode):
    counterNode = functionNode.get_child("counter")
    try:
        val = int(counterNode.get_value())
    except:
        val = 0
    counterNode.set_value(val+1)



def periodic_timer(functionNode):
    # this function never ends until we get the signal "stop"
    signalNode = functionNode.get_child("control").get_child("signal")
    timeoutNode = functionNode.get_child("lastTimeout")
    durationNode = functionNode.get_child("lastDuration")
    counterNode = functionNode.get_child("executionCounter")

    sleep_time = float(functionNode.get_child("periodSeconds").get_value())
    running = True
    while True:
        #execute the functions
        startTime = datetime.datetime.now()
        timeoutNode.set_value(startTime.isoformat())
        for node in functionNode.get_child("target").get_leaves():
            print("execute",node.get_name())
            node.execute()
        durationNode.set_value((datetime.datetime.now()-startTime).total_seconds())
        counterNode.set_value(counterNode.get_value()+1)
        if signalNode.get_value() == "stop":
            signalNode.set_value("nosignal")
            break
        time.sleep(sleep_time)
    return True



def observer_function(functionNode):
    subjectNodes = functionNode.get_child("subject").get_targets() # this is the subject to watch
    properties = functionNode.get_child("properties").get_value()
    statusNode = functionNode.get_child("lastStatus")
    currentStatus = {}
    for node in subjectNodes:
        nodeStatus = {}
        if "leaves" in properties:
            nodeStatus["leaves"]=[child.get_id() for child in node.get_leaves()]
        if "value" in properties:
            nodeStatus["value"]=node.get_value()
        if "children" in properties:
            nodeStatus["children"] = [child.get_id() for child in node.get_children()]
        currentStatus[node.get_id()]=copy.deepcopy(nodeStatus)
    if statusNode.get_value() == None:
        #this is the first time
        statusNode.set_value(copy.deepcopy(currentStatus))
    else:
        #we must compare
        if json.dumps(statusNode.get_value()) != json.dumps(currentStatus):
            #a change!
            counterNode = functionNode.get_child("updateCounter")
            counterNode.set_value(counterNode.get_value()+1)
            for node in functionNode.get_child("onUpdate").get_leaves():
                node.execute()
            statusNode.set_value(copy.deepcopy(currentStatus))
    return True

