import requests
import pathlib
from datetime import datetime
# datetime object containing current date and time
now = datetime.now()

from bbrest import BbRest
key = "your-key-goes-here"
secret = "your-secret-goes-here"
learnfqdn = "your-blackboard-url"
bb = BbRest(key, secret, "https://"+ str(learnfqdn) +"")  # Does a lot! Get the system version, pull in the functions from dev portal, 2-legged authentication w/ caching of token.

name = input("Enter file:")
textRow = open(name)
log = open("bb-rest-enrollment-testing-log.txt", "a")
debug_log = open("bb-rest-enrollment-testing-debug.txt", "a")
dt_start_string = now.strftime("%d/%m/%Y %H:%M:%S")
log_start_timedate = "Script was started at: " + dt_start_string + '.\n\n'
log.write(log_start_timedate)

# Setting a counter to know how many enrollments were processed.
totalCount = 0
successCount = 0
errorCount = 0
createCount = 0
updateCount = 0

for line in textRow:

    # Read a line into the script and remove any trailing characters.
    line = line.rstrip()

    # Check to see the line isn't blank.
    if len(line) < 1:
        continue
    
    # Create an array from the line splitting at the commas.
    value = line.split(',')
    
    # Take the value array and assign it to variables.
    course = value[0]
    userid = value[1]
    role = value[2]
    available = value[3]

    # Setting datasource to use SYSTEM for the enrollments.
    dataSource = "_2_1"

    # Check to see if available is 'Y' or 'N' and update to full word

    if available == 'Y' or available == 'Yes' or available == 'YES':
        available = "Yes"
    elif available == 'N' or available == 'No' or available == 'NO':
        available = "No"
    else:
        logEvent = 'File contains incorrect characters in the availability column. Stopping...\n\n'
        log.write(logEvent)
        print(logEvent)
        break


    # Check to see if Rest API bearer token is expired.
    s = bb.is_expired()
    if s == True:
        # Refresh bearer token
        ref = bb.refresh_token()

    # Check to see if the course exists and if it's disabled.
    courseCheck = bb.GetCourse(courseId=course)
    courseCheckStatus = courseCheck.status_code
    
    # 404 code means the course doesn't exist in Blackboard. 
    if courseCheckStatus != 200:
        # Logging the event.
        logEvent = course + ' does not exist in Blackboard or isn\'t properly formatted in the feed file. Skipping enrollment...\n\n'
        log.write(logEvent)
        totalCount = totalCount + 1
        errorCount = errorCount + 1

    else:
        courseOutput = courseCheck.json()
        courseAvail = courseOutput['availability']['available']

        if (courseAvail == 'Disabled'):
            # Logging the event
            logEvent = course + ' has been disabled in Blackboard. Enrollments are not allowed. Skipping enrollment for ' + userid + '.\n\n'
            log.write(logEvent)
            totalCount = totalCount + 1
            errorCount = errorCount + 1

        else:
            userCheck = bb.GetUser(userId=userid)
            userCheckStatus = userCheck.status_code

            if userCheckStatus != 200:
                logEvent = userid + ' does not exist in Blackboard or isn\'t properly formatted in the feed file. Skipping enrollment...\n\n'
                log.write(logEvent)
                totalCount = totalCount + 1
                errorCount = errorCount + 1
        
        
        
        
            # Check the status code from the Membership result and either create the membership or update it.
            enrollCheck = bb.GetMembership(courseId=course,userId=userid)
            enrollCheckStatus = enrollCheck.status_code

            # 404 status means membership doesn't exist, so create the membership in Blackboard.
            if enrollCheckStatus == 404:
                r = bb.CreateMembership(courseId=course,userId=userid,payload={"dataSourceId": dataSource,"availability": {"available": available},"courseRoleId": role})
                statusCode = r.status_code
                totalCount = totalCount + 1
                successCount = successCount + 1
                createCount = createCount + 1

                # Logging the membership creation event.
                logEvent = userid + ' has been enrolled as ' + role + ' in the course ' + course + ' with the availability of ' + available + '.\nBlackboard provided the following response status code ' + str(statusCode) + '.\n\n'
                log.write(logEvent)

            # 200 status means membership exists, so update the membership in Blackboard.
            elif enrollCheckStatus == 200:
                r = bb.UpdateMembership(courseId=course,userId=userid,payload={"dataSourceId": dataSource,"availability": {"available": available},"courseRoleId": role})
                statusCode = r.status_code
                totalCount = totalCount + 1
                successCount = successCount + 1
                updateCount = updateCount + 1

                # Logging the membership update event.
                logEvent = userid + ' has been enrolled as ' + role + ' in the course ' + course + ' with the availability of ' + available + '.\nBlackboard provided the following response status code ' + str(statusCode) + '.\n\n'
                log.write(logEvent)

            else:
                enrollOutput = enrollCheck.json()
                enrollCheckMsg = enrollOutput['message']
                print('Error: ' + str(enrollCheckStatus) + ' was provided from Blackboard when searching for ' + course + ' with the message \"' + enrollCheckMsg + '\". \n Skipping record: ' + str(value) + '.')
                totalCount = totalCount + 1
                errorCount = errorCount + 1

finalOutput = 'The script has completed.\nINFO: ' + str(totalCount) + ' records were processed.\nSUCCESS: ' + str(successCount) + ' records were processed successfully.\nFAIL: ' + str(errorCount) + ' records failed during processing.\nCREATE: ' + str(createCount) + ' enrollments created in the process.\nUPDATE: ' + str(updateCount) + ' enrollments update in the process.\n\n'
log.write(finalOutput)

# datetime object containing current date and time
now = datetime.now()

dt_end_string = now.strftime("%d/%m/%Y %H:%M:%S")
log_end_timedate = "Script finished processing at: " + dt_end_string + '.\n\n'
log.write(log_end_timedate)
log.close()
print(log_end_timedate)
print(finalOutput)