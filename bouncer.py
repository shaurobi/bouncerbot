import csv, requests, json,datetime,pytz

myToken = "Bearer xxx"
botToken= "Bearer xxx"

# specify the ID of the space below, 
eventSpace = "xxx"

#insert meeting number below
meetingNumber = "xxxxxxxxx"

#specify attendee list for reporting late
attendeelist = "attendees.csv"
#specify local registration list, with emails included. 
regolist = "finalregistration1.csv"

#gets meeting ID for API purposes from meeting number. 
def getmeetingID(authtoken, meetingnumber):
    url = "https://webexapis.com/v1/meetings"
    headers = {'Authorization': authtoken}
    params = {'meetingNumber':meetingnumber}
    response = requests.request("GET", url, headers=headers, params = params)
    meetingInfo = response.json()
    print("Getting Meeting Info")
    print(meetingInfo)
    meetingID = meetingInfo["items"][0]['id']
    return meetingID

#gets paricipant list as a JSON representation.
def getparticipants(meetingID, authtoken):
    url = "https://webexapis.com/v1/meetingParticipants"
    headers = {'Authorization': authtoken}
    params = {'meetingId':meetingID}
    response = requests.request("GET", url, headers=headers, params = params)
    return response.json()

#simple writer to append participants line by line to a CSV
def appendRow(filename, elem):
    # Open file in append mode
    with open(filename, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = csv.writer(write_obj)
        #print(f'printing {elem}')
        # Add contents of list as last row in the csv file
        csv_writer.writerow(elem)

#iterates over participant JSON rep to write to a CSV file
def writeparticipants(participantsjson):
    details = []
    for items in participantsjson["items"]:
        #print(items["email"],items["displayName"])
        details.append(items["email"])
        details.append(items["displayName"])
        details.append("No")
        #specify your own timezone appropriately
        tz = pytz.timezone('Australia/Melbourne')
        joinedTime = items["devices"][0]["joinedTime"]
        #print(joinedTime)
        joinedTime = int(joinedTime)
        joinedTime = joinedTime/1000
        datetime_time = datetime.datetime.fromtimestamp(joinedTime)
        details.append(datetime_time)
        #print(details)
        appendRow(attendeelist,details)
        details = []

#function for posting messages to space
def postMessage(text,space,token):
    url = "https://api.ciscospark.com/v1/messages"
    payload={'roomId': space,
    'text': text}
    headers = {
            'Authorization': token
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

#iterates over JSON file to provide alerts on unregistered attendees in meeting, with email.
def alertJson(attendeejson,registrationlist,token,space):
    # open registration list
    registrationEmails = []
    with open(registrationlist) as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count +=1
            else:
                registrationEmails.append(row[3])
                line_count +=1
        print(f'list of registered emails {registrationEmails}') 
    print(attendeejson)
    for items in attendeejson["items"]:
        print(f'Attendee  {items["displayName"]}, with email address {items["email"]}, and meeting state as {items["state"]}')
        if items["state"] == "joined":
            #including domain here for export purposes
            if "cisco" in items["email"]:
                print(f'Ignoring Attendee {items["displayName"]} due to Cisco domain')
            elif items["email"] not in registrationEmails:
                print(f' MATCH on {items["email"]},{items["displayName"]} and state {items["state"]}')
                message = f'Alert, {items["displayName"]} is an unexpected attendee with email {items["email"]}'
                print(f'sending {message}')
                postMessage(message,space,token)


#Actual alerts 
postMessage("Beep Borp, here we go! Getting the attendee list!",eventSpace,botToken)
print("Getting Meeting ID")
meetingID = getmeetingID(myToken,meetingNumber)
print(meetingID)
print("Getting participants")
participants = getparticipants(meetingID,myToken)
print("Writing to file")
#writing this JSON rep to a file for archive purposes.
f = open("participants.json.txt", "a")
f.write(str(participants))
f.close()

print("ALERTING ONLY ON UNEXPECTED DOMAINS")
alertJson(participants,"registrations.csv",botToken,eventSpace)

#print("ALERTING ON ALL DOMAINS, DANGER DANGER DANGER")
#This will alert on all domains
#alertJsonAll(participants,"registrations.csv",botToken,eventSpace)

#line for writing participants to CSV files for later.
writeparticipants(participants)
