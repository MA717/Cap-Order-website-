import sqlite3  
from datetime import datetime as time
from hashlib import sha512

def WriteCustomerToDB(form):
    db = sqlite3.connect('DB.db3')
    id = db.execute('SELECT COUNT(*) FROM CUSTOMERS').fetchone()[0] + 1

    h  = sha512(form['Password'].encode()).hexdigest()
    try:
        query = f'''INSERT INTO CUSTOMERS VALUES
              ( {id},
               '{form['Fname']}',
               '{form['Mname']}',
               '{form['Lname']}',
               '{form['Email']}',
               '{form['PhoneNum']}',
               '{h}', 5)''' 

        db.execute(query)
        db.commit()
        return 1
    except:# Exception as e:
        return 0
    finally:
        db.close()

def WriteDriverToDB(form):
    db = sqlite3.connect('DB.db3')
    id = db.execute('SELECT COUNT(*) FROM DRIVERS').fetchone()[0] + 1

    h  = sha512(form['Password'].encode()).hexdigest()
    try:
        query = f'''INSERT INTO DRIVERS VALUES
              ( 
                {id},
               '{form['Fname']}',
               '{form['Mname']}',
               '{form['Lname']}',
               '{form['Email']}',
               '{form['PhoneNum']}',
               '{h}', 
               5,
               '{form['LiNum']}',
               '{form['NationalID']}'
               )''' 
        
        db.execute(query)

        db.execute(f'''
                        INSERT INTO CARS VALUES
                        (
                            '{form['CarLicPlate']}',
                            '{form['CarType']}',
                             {form['CarCapP']}  ,
                             {form['CarCapC']}   ,
                            '{form['CarDescr']}',
                            {id}
                        )
                    ''')
        db.commit()
        return 1
    except:
        return 0
    finally:
        db.close()

def UserExists(email, passs,type):
    db = sqlite3.connect('DB.db3')

    res = db.execute(f"SELECT Fname, Password FROM {type} WHERE Email = '{email}'").fetchone()
    db.close()

    if res is None: return None 
    
    if str(res[1]) != sha512(passs.encode()).hexdigest(): 
        return -1

    return res[0]

def GetLocations():
    db = sqlite3.connect('DB.db3')

    locs = db.execute("SELECT * FROM LOCATIONS").fetchall()

    db.close() 
    return locs 

def WriteTripRequestToDB(form, customer_email):
    db = sqlite3.connect('DB.db3')
    
    customer_ID  = db.execute(f'''SELECT ID FROM CUSTOMERS WHERE Email = '{customer_email}' ''').fetchone()[0]
    pick_up_id   = db.execute(f'''SELECT ID FROM LOCATIONS WHERE Street = '{form["PickUpStreet"]}' ''').fetchone()[0]
    drop_off_id  = db.execute(f'''SELECT ID FROM LOCATIONS WHERE Street = '{form["DropOffStreet"]}' ''').fetchone()[0]
    try:
        query = f'''INSERT INTO TRIP_REQUESTS VALUES
              ( {customer_ID},
               '{form["TripTime"]}',
                {form['Num_Pass']},
               '{form['Cargo']}',
               '{pick_up_id}',
               '{drop_off_id}')''' 
        db.execute(query)
        db.commit()
        return 1
    except:
        return 0
    finally:
        db.close()

def GetAllTripsForUser(email):
    db = sqlite3.connect('DB.db3')

    query = f'''SELECT TRIP_REQUESTS.Start_time, P.City, P.District, P.Street, D.City, D.District, D.Street

                FROM CUSTOMERS, TRIP_REQUESTS, LOCATIONS AS P, LOCATIONS AS D

                WHERE CUSTOMERS.Email = '{email}' AND CUSTOMERS.ID = TRIP_REQUESTS.Customer_ID
                    AND TRIP_REQUESTS.Pick_up = P.ID AND TRIP_REQUESTS.Drop_off = D.ID'''
    
    t_reqs = db.execute(query)

    query = f'''SELECT TR.Time, P.City, P.District, P.Street, D.City, D.District, D.Street, 
                       TR.Fee,  DR.Email, (SELECT value FROM RATINGS WHERE Driver_ID = DR.ID AND Customer_ID = C.ID AND Trip_Date = TR.Time AND WhoRated = TRUE) 

                FROM CUSTOMERS AS C, TRIPS AS TR, LOCATIONS AS P, LOCATIONS AS D, DRIVERS AS DR

                WHERE   C.Email = '{email}' AND C.ID = TR.Customer_ID
                    AND TR.Pick_up = P.ID AND TR.Drop_off = D.ID
                    AND DR.ID    = TR.Driver_ID'''
                    

    ts = db.execute(query)
    
    trip_requests = []
    for trip_request in t_reqs:
        t = {}
        t["start_date"] = trip_request[0]
        t["pick_up"]    = f"{trip_request[1]} , {trip_request[2]} , {trip_request[3]}"
        t["drop_off"]   = f"{trip_request[4]} , {trip_request[5]} , {trip_request[6]}" 
        trip_requests.append(t)
    
    trips = []
    for trip in ts:
        t = {}
        t["start_date"] = trip[0]
        t["pick_up"]    = f"{trip[1]} , {trip[2]} , {trip[3]}"
        t["drop_off"]   = f"{trip[4]} , {trip[5]} , {trip[6]}"  
        t["Fee"]        = trip[7]
        t["Driv_email"] = trip[8]
        t["rating"]     = trip[9]
        trips.append(t)
    
    db.close()
    return trip_requests, trips

def GetAllAvailableTripsForDriver(email):
    db = sqlite3.connect('DB.db3')

    id = db.execute(f"SELECT ID FROM DRIVERS WHERE Email = '{email}'").fetchone()[0]

    query = f'''SELECT C.Email, P.City, P.District, P.Street, D.city, D.District, D.Street , TR.Start_time

                FROM   CUSTOMERS AS C, TRIP_REQUESTS AS TR, LOCATIONS AS P, LOCATIONS AS D

                WHERE          C.ID = TR.Customer_ID 
                       AND     P.ID = TR.Pick_up AND D.ID = TR.Drop_off
                       AND     NOT EXISTS (
                                                SELECT 1
                                                FROM   TRIP_OFFERS

                                                WHERE  TRIP_OFFERS.Customer_ID = C.ID 
                                                AND    TRIP_OFFERS.Trip_time   = TR.Start_time
                                                AND    TRIP_OFFERS.Driver_ID   = {id}
                                               )
            '''
    data = db.execute(query)

    trips = []
    for row in data:
        trip = {}
        trip['Customer email'] = row[0]
        trip['Pick up location'] = f"{row[1]} , {row[2]} , {row[3]}"
        trip['Drop off location'] =f"{row[4]} , {row[5]} , {row[6]}" 
        trip['Starts on'] = row[7]

        trips.append(trip)

    db.close()
    return trips 

def WriteTripOfferToDB(form):
    db = sqlite3.connect('DB.db3')

    cust_id = db.execute(f"SELECT ID FROM CUSTOMERS WHERE Email = '{form['Customer_email']}'").fetchone()[0]
    driv_id = db.execute(f"SELECT ID FROM DRIVERS   WHERE Email = '{form['Driver_email']}'").fetchone()[0]
    try:
        query = f''' INSERT INTO TRIP_OFFERS VALUES ({driv_id},{cust_id},'{form["Trip_date"]}',FALSE,{form["Fee"]})''' 
        db.execute(query)
        db.commit()
        return 1
    except:
        return 0
    finally:
        db.close()

def GetAllConfirmedTripsDriver(email):
    db   = sqlite3.connect('DB.db3')

    id   = db.execute(f'''SELECT ID FROM DRIVERS WHERE Email = '{email}' ''').fetchone()[0]

    data =  db.execute(f'''
                            SELECT C.Email,
                                   TR.Time, TR.Fee, TR.Num_passengers, TR.Cargo, 
                                   P.City, P.District, P.Street, D.City, D.District, D.Street,
                                   (SELECT value FROM RATINGS WHERE Driver_ID = {id} AND Customer_ID = C.ID AND Trip_Date = TR.Time AND WhoRated = FALSE)

                                   
                            FROM TRIPS AS TR, CUSTOMERS AS C , LOCATIONS AS P, LOCATIONS AS D

                            WHERE TR.Driver_ID = {id}
                            AND   TR.Customer_ID = C.ID
                            AND   TR.Pick_up     = P.ID 
                            AND   TR.Drop_off    = D.ID  
                         ''')
    trips = []
    for row in data:
        trip = {}
        trip['Customer_Email'] = row[0] 
        trip['Time']           = row[1]
        trip['fee']            = row[2]
        trip['passengers']     = row[3]
        trip['cargo']          = row[4]

        trip['Pick_Up']  = f"{row[5]} , {row[6]} , {row[7]}"
        trip['Drop_Off'] = f"{row[8]} , {row[9]} , {row[10]}" 
        trip['rating']   = row[11] 
        trips.append(trip)
    db.close()
    return trips

def GetAllOffersMadeByDriver(email):
    db   = sqlite3.connect('DB.db3')
    
    id   = db.execute(f"SELECT ID FROM DRIVERS WHERE Email = '{email}'").fetchone()[0]

    query = f'''
                        SELECT CUSTOMERS.Email, TRIP_OFFERS.Trip_time, TRIP_OFFERS.Is_Accepted, TRIP_OFFERS.Fee

                        FROM TRIP_OFFERS, CUSTOMERS 

                        WHERE   TRIP_OFFERS.Driver_ID   = {id}
                        AND     CUSTOMERS.ID            = TRIP_OFFERS.Customer_ID

                      '''
    data = db.execute(query) 
    offers = []
    for row in data:
        offer = {}

        offer['Customer_Email'] = row[0]
        offer['Trip_time']      = row[1]
        offer['Is_Accepted']    = row[2]
        offer['Fee']            = row[3]

        offers.append(offer)
    db.close()
    return offers

def GetAllOffersForTripCustomer(form):
    db = sqlite3.connect('DB.db3') 

    id = db.execute(f"SELECT ID FROM CUSTOMERS WHERE Email = '{form['Customer_email']}'").fetchone()[0]
    q  = f'''
                SELECT DRIVERS.Email , TRIP_OFFERS.Fee 

                FROM   TRIP_OFFERS,DRIVERS

                WHERE  TRIP_OFFERS.Driver_ID   = DRIVERS.ID 
                AND    TRIP_OFFERS.Customer_ID = {id} 
                AND    TRIP_OFFERS.Trip_time   = '{form['Trip_date']}'
                AND    TRIP_OFFERS.Is_Accepted = FALSE
        '''
    data = db.execute(q)

    offers = []
    for row in data:
        offer = {}
        offer['Driver_Email'] = row[0]
        offer['Fee']          = row[1]
        offers.append(offer)

    db.close()
    return offers

def ChangeOfferStatus(customer_email,date, driver_email):
    db = sqlite3.connect('DB.db3')
    driver_id   = db.execute(f"SELECT ID FROM DRIVERS WHERE Email = '{driver_email}' ").fetchone()[0]
    customer_id = db.execute(f"SELECT ID FROM CUSTOMERS WHERE Email = '{customer_email}'").fetchone()[0]
    try:
        db.execute(f'''
                    UPDATE TRIP_OFFERS 
                    SET Is_Accepted = TRUE 

                    WHERE Driver_ID   = {driver_id}
                    AND   Customer_ID = {customer_id}
                    AND   Trip_time   = '{date}'
                    ''')

        db.commit()
        return 1
    except:
        return 0 
    finally:
        db.close()

def ConfrimAcceptedOffer(driver_email, customer_email, trip_time):
    db = sqlite3.connect('DB.db3')

    driv_id = db.execute(f'''SELECT ID FROM DRIVERS   WHERE Email='{driver_email}'   ''').fetchone()[0]
    cust_id = db.execute(f'''SELECT ID FROM CUSTOMERS WHERE Email='{customer_email}' ''').fetchone()[0]

    data = db.execute(f'''
                        SELECT TRIP_OFFERS.Fee,
                               TRIP_REQUESTS.Pick_up,
                               TRIP_REQUESTS.Drop_off,
                               TRIP_REQUESTS.Num_passengers,
                               TRIP_REQUESTS.Cargo
                               

                        FROM   TRIP_OFFERS, TRIP_REQUESTS

                        WHERE TRIP_OFFERS.Customer_ID = {cust_id} AND TRIP_OFFERS.Driver_ID = {driv_id}
                        AND   TRIP_OFFERS.Trip_time   = '{trip_time}'
                        AND   TRIP_OFFERS.Customer_ID = TRIP_REQUESTS.Customer_ID
                        AND   TRIP_OFFERS.Trip_time   = TRIP_REQUESTS.Start_time
                        ''').fetchone()
    if data is None : 
        db.close()
        return 0

    try:
        c = db.execute("PRAGMA FOREIGN_KEYS = on")
        c.execute(f"DELETE FROM TRIP_REQUESTS WHERE Customer_ID = {cust_id} AND Start_time = '{trip_time}'") 

        db.execute(f'''
                    INSERT INTO TRIPS VALUES (
                        {cust_id}, {driv_id}, '{trip_time}',
                        {data[0]}, {data[1]}, {data[2]},
                        {data[3]}, '{data[4]}'
                    )
                ''')
        db.commit()
        return 1
    except:
        return 0
    finally:
        db.close()
        

def WriteTripComplaintByDriver(form):
    db = sqlite3.connect('DB.db3')

    cust_id = db.execute(f"SELECT ID FROM CUSTOMERS WHERE Email = '{form['Customer_email']}' ").fetchone()[0]
    driv_id = db.execute(f"SELECT ID FROM DRIVERS   WHERE Email = '{form['Driver_email']}'").fetchone()[0]

    query = f'''
                    INSERT INTO COMPLAINTS VALUES (
                        {cust_id},
                        {driv_id},
                       '{form['Trip_date']}',
                        FALSE,
                        NULL,
                        '{form['Complaint']}',
                        '{time.now().isoformat()[0:16]}',
                        FALSE
                    )
                '''
    try:
         db.execute(query)
         db.commit()
    except:
         pass
    finally:
         db.close()

def WriteTripComplaintByCustomer(form):
    db = sqlite3.connect('DB.db3')

    cust_id = db.execute(f"SELECT ID FROM CUSTOMERS WHERE Email = '{form['Customer_email']}' ").fetchone()[0]
    driv_id = db.execute(f"SELECT ID FROM DRIVERS   WHERE Email = '{form['Driver_email']}'").fetchone()[0]

    query = f'''
                    INSERT INTO COMPLAINTS VALUES (
                        {cust_id},
                        {driv_id},
                       '{form['Trip_date']}',
                        FALSE,
                        NULL,
                        '{form['Complaint']}',
                        '{time.now().isoformat()[0:16]}',
                        TRUE
                    )
                '''
    try:
         db.execute(query)
         db.commit()
    except:
         pass
    finally:
         db.close()

def ChangePasswordOfUser(old,new,type,email):
    db = sqlite3.connect('DB.db3')
    
    key_name = "ID"         if type == "CUSTOMERS" or type == "DRIVERS" else     \
               "Admin_key"  if type == "ADMINS" else                              \
               "Manager_ID" if type == "MANAGERS" else                             \
               "Employee_ID"

    r = db.execute(f"SELECT {key_name}, Password FROM {type} WHERE Email = '{email}' ").fetchone()
    id, old_pass = r[0] , r[1]

    if sha512(old.encode()).hexdigest() != old_pass:
        return -1
    
    query = f'''UPDATE {type}

                SET Password = '{sha512(new.encode()).hexdigest()}' 

                WHERE {key_name} = {id}
            '''
    
    db.execute(query)
    db.commit()
    db.close()

    return 1 

def AddOrUpdateRatingByCustomer(form):

    db = sqlite3.connect('DB.db3')

    cust_id = db.execute(f"SELECT ID FROM CUSTOMERS WHERE Email = '{form['Customer_email']}' ").fetchone()[0]
    driv_id = db.execute(f"SELECT ID FROM DRIVERS   WHERE Email = '{form['Driver_email']}'").fetchone()[0]

    does_exist = db.execute(f'''SELECT 1 FROM RATINGS WHERE
                                Driver_ID   = {driv_id}
                            AND Customer_ID = {cust_id}
                            AND Trip_Date   ='{form['Trip_date']}' 
                            AND WhoRated    = TRUE   
                            ''').fetchone()
    #This is the first ratings
    if(does_exist is None):
        db.execute(f'''
                    INSERT INTO RATINGS VALUES (
                        {driv_id},
                        {cust_id},
                       '{form['Trip_date']}',
                        TRUE,
                        {form['rating']}
                    )
                    ''')       
    else:
        db.execute(f'''
                    UPDATE RATINGS
                    SET value = {form['rating']}

                    WHERE   Driver_ID       = {driv_id}
                            AND Customer_ID = {cust_id}
                            AND Trip_Date   ='{form['Trip_date']}' 
                            AND WhoRated    = TRUE   
                    ''')
        
    db.execute(f'''
                    UPDATE DRIVERS 
                    SET    Rating = ( SELECT AVG(value) FROM RATINGS WHERE Driver_ID = {driv_id} )

                    WHERE  ID = {driv_id}
                ''')
    db.commit()
    db.close()

def AddOrUpdateRatingByDriver(form):
    db = sqlite3.connect('DB.db3')

    cust_id = db.execute(f"SELECT ID FROM CUSTOMERS WHERE Email = '{form['Customer_email']}' ").fetchone()[0]
    driv_id = db.execute(f"SELECT ID FROM DRIVERS   WHERE Email = '{form['Driver_email']}'").fetchone()[0]

    does_exist = db.execute(f'''SELECT 1 FROM RATINGS WHERE
                                Driver_ID   = {driv_id}
                            AND Customer_ID = {cust_id}
                            AND Trip_Date   ='{form['Trip_date']}' 
                            AND WhoRated    = FALSE 
                            ''').fetchone()
    #This is the first ratings
    if(does_exist is None):
        db.execute(f'''
                    INSERT INTO RATINGS VALUES (
                        {driv_id},
                        {cust_id},
                       '{form['Trip_date']}',
                        FALSE,
                        {form['rating']}
                    )
                    ''')       
    else:
        db.execute(f'''
                    UPDATE RATINGS
                    SET value = {form['rating']}

                    WHERE   Driver_ID       = {driv_id}
                            AND Customer_ID = {cust_id}
                            AND Trip_Date   ='{form['Trip_date']}' 
                            AND WhoRated    = FALSE   
                    ''')
        
    db.execute(f'''
                    UPDATE CUSTOMERS 
                    SET    Rating = ( SELECT AVG(value) FROM RATINGS WHERE Customer_ID = {cust_id} )

                    WHERE  ID = {cust_id}
                ''')
    db.commit()
    db.close()
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------


def WriteNewEmployeeToDB(form):

    db = sqlite3.connect('DB.db3')

    id = db.execute("SELECT COUNT(*) FROM APPLICANTS").fetchone()[0] + 1

    q  = f'''
            INSERT INTO APPLICANTS VALUES (
                 {id},
                '{form['fname']}',
                '{form['lname']}',
                '{form['mname']}',
                '{form['email']}',
                '{form['phonenum']}',
                '{sha512(form['pass'].encode()).hexdigest()}',
                 {int("SignUpMan" in form)}
            )
          '''
    try:
        db.execute(q)
        db.commit()
        return 1
    except:
        return 0
    finally:
        db.close()

def AcceptApplyingManager(man_email, approving_manager_email):
    db = sqlite3.connect('DB.db3')
    
    mang = db.execute(f'''SELECT Fname, Mname, Lname, Email, Phonenum, Password 
                          FROM APPLICANTS 
                          
                          WHERE Is_Manager = TRUE 
                          AND   Email = '{man_email}'       ''').fetchone()
    
    try:
        db.execute(f'''
                        INSERT INTO MANAGERS VALUES (
                            (SELECT COUNT(*)+1 FROM MANAGERS),
                            '{mang[0]}',
                            '{mang[1]}',
                            '{mang[2]}',
                            '{mang[3]}',
                            '{mang[4]}',
                            '{mang[5]}',
                             (SELECT Manager_ID FROM MANAGERS WHERE Email = '{approving_manager_email}')
                        )
                    ''')
        db.execute(f'''
                        DELETE FROM APPLICANTS WHERE Email = '{man_email}'
                    ''') 
        db.commit()
        return 1                
    except :
        return 0
    finally:
        db.close()       
    
def GetAllApplyingManagers():
    db = sqlite3.connect('DB.db3')

    data  =  db.execute("SELECT * FROM APPLICANTS WHERE Is_Manager = TRUE")
    

    applying_managers = []
    for row in data:
        applying_manager = {}
        applying_manager['name'] = row[1] + " " + row[3] + " " + row[2]
        applying_manager['email'] = row[4]
        applying_manager['phonenum'] = row[5]
        
        applying_managers.append(applying_manager)
    db.close()
    return applying_managers

def AcceptApplyingSupport(supp_email, approving_manager_email):
    db = sqlite3.connect('DB.db3')
    
    supp = db.execute(f'''SELECT Fname, Mname, Lname, Email, Phonenum, Password 
                          FROM APPLICANTS 
                          
                          WHERE Is_Manager = FALSE 
                          AND   Email = '{supp_email}'       ''').fetchone()
    
    try:
        db.execute(f'''
                        INSERT INTO SUPPORT VALUES (
                            (SELECT COUNT(*)+1 FROM MANAGERS),
                            '{supp[0]}',
                            '{supp[1]}',
                            '{supp[2]}',
                            '{supp[3]}',
                            '{supp[4]}',
                            '{supp[5]}',
                             (SELECT Manager_ID FROM MANAGERS WHERE Email = '{approving_manager_email}')
                        )
                    ''')
        db.execute(f'''
                        DELETE FROM APPLICANTS WHERE Email = '{supp_email}'
                    ''') 
        db.commit()
        return 1                
    except:
        return 0
    finally:
        db.close()

def GetAllApplyingSupport():
    db = sqlite3.connect('DB.db3')

    data  =  db.execute("SELECT * FROM APPLICANTS WHERE Is_Manager = FALSE")
    

    applying_support = []
    for row in data:
        support = {}
        support['name'] = row[1] + " " + row[3] + " " + row[2]
        support['email'] = row[4]
        support['phonenum'] = row[5]
        
        applying_support.append(support)

    db.close()
    return applying_support

def GetAllSupportsUnderManager(email):
    db = sqlite3.connect('DB.db3')

    id = db.execute(f"SELECT Manager_ID FROM MANAGERS WHERE Email = '{email}'").fetchone()[0]
    data = db.execute(f'''
               with recursive MANAGER_TREE (Manager_ID) 
                                AS (
                                    SELECT Manager_ID
                                    FROM   MANAGERS 
                                    WHERE  Manager_ID = {id} 
                                    
                                    UNION ALL
                                    
                                    SELECT M.Manager_ID
                                    FROM   MANAGERS as M, MANAGER_TREE as MT
                                    WHERE  M.Hired_By = MT.Manager_ID
                                )
                                
               SELECT Fname, Mname, Lname, Email, Phone_num 
               FROM   SUPPORT , MANAGER_TREE

               WHERE SUPPORT.Hired_By = MANAGER_TREE.Manager_ID
                ''')

    support = []
    for row in data:
        supp = {}
        supp['name'] = row[0] + " " + row[1] + " " + row[2]
        supp['Email'] = row[3]
        supp['Phonenum'] = row[4]

        support.append(supp)
    
    db.close()
    return support

def GetAllManagersUnderManager(email):
    db = sqlite3.connect('DB.db3')

    id = db.execute(f"SELECT Manager_ID FROM MANAGERS WHERE Email = '{email}'").fetchone()[0]
    data = db.execute(f'''
               with recursive MANAGER_TREE (Manager_ID, Fname, Mname, Lname, Email, Phonenum) 
                                AS (
                                    SELECT Manager_ID, Fname, Mname, Lname, Email, Phone_num
                                    FROM   MANAGERS 
                                    WHERE  Manager_ID = {id} 
                                    
                                    UNION ALL
                                    
                                    SELECT M.Manager_ID, M.Fname, M.Mname, M.Lname, M.Email, M.Phone_num
                                    FROM   MANAGERS as M, MANAGER_TREE as MT
                                    WHERE  M.Hired_By = MT.Manager_ID
                                )
                                
               SELECT * FROM MANAGER_TREE
                ''')

    data.fetchone()
    
    managers = []
    for row in data:
        manager = {}
        manager['name'] = row[1] + " " + row[2] + " " + row[3]
        manager['Email'] = row[4]
        manager['Phonenum'] = row[5]

        managers.append(manager)
    
    db.close()
    return managers

def FireEmployee(email, type):
    db = sqlite3.connect('DB.db3')
    try:
        q  = f'''
                DELETE FROM {type}

                WHERE Email = '{email}'
                '''
        db.execute(q)
        db.commit()
        return 1
    except:
        return 0
    finally:
        db.close()

def AssignComplaintToSupport(email, complaint_info):
    db = sqlite3.connect('DB.db3')
    try:
        q = f'''
                UPDATE COMPLAINTS

                SET    Assigned_To = (SELECT Employee_ID FROM SUPPORT WHERE Email = '{email}')

                WHERE  Customer_ID =  {complaint_info['cust_id']}
                AND    Driver_ID   =  {complaint_info['driv_id']}
                AND    Trip_Time   = '{complaint_info['t_time']}'
                AND    Time_Filed  = '{complaint_info['f_time']}'
                AND    Who_Filed   =  {int(complaint_info['whoComplained'] == "Customer")}
                '''
        db.execute(q)
        db.commit()
        return 1
    except:
        return 0
    finally:
        db.close()

def MarkComplaintSolved(complaint_info):
    db = sqlite3.connect('DB.db3')
    try:
        q = f'''
                UPDATE COMPLAINTS

                SET    Is_Solved = TRUE

                WHERE  Customer_ID =  {complaint_info['cust_id']}
                AND    Driver_ID   =  {complaint_info['driv_id']}
                AND    Trip_Time   = '{complaint_info['t_time']}'
                AND    Time_Filed  = '{complaint_info['f_time']}'
                AND    Who_Filed   =  {int(complaint_info['whoComplained'] == "Customer")}
                '''
        db.execute(q)
        db.commit()
        return 1
    except:
        return 0
    finally:
        db.close()

def GetAllUnresolvedComplaintsForSupport(email = None):
    db = sqlite3.connect('DB.db3')

    id = "NULL"
    if(email is not None): id = db.execute(f"SELECT Employee_ID FROM SUPPORT WHERE Email = '{email}'").fetchone()[0]
    q  = f'''
            SELECT 
            COM.Customer_ID, COM.Driver_ID, COM.Trip_Time, COM.Time_Filed, COM.Who_Filed, COM.Description,
                   C.Fname, C.Mname, C.Lname, C.Email, C.Phone_num,
                   D.Fname, D.Mname, D.Lname, D.Email, D.Phone_num

            FROM   COMPLAINTS AS COM, CUSTOMERS AS C, DRIVERS AS D

            WHERE {f"Assigned_To = {id} " if id != "NULL" else "Assigned_To is NULL"}
                  
                  AND COM.Customer_ID = C.ID 
                  AND COM.Driver_ID   = D.ID 
                  AND COM.Is_Solved   = FALSE
            '''
    data = db.execute(q)

    complaints = []
    for row in data:
        complaint = {}

        complaint['cust'] = {"ID": row[0], 
                             "Name": row[6] + " " + row[7] + " " + row[8], 
                             "Email": row[9], 
                             "PhoneNum": row[10]}

        complaint['driv'] = {"ID": row[1], 
                             "Name": row[11] + " " + row[12] + " " + row[13], 
                             "Email": row[14], 
                             "PhoneNum": row[15]}

        complaint['info'] = {"Trip_Time"  : row[2], 
                             "Filing_Time": row[3],
                             "Who_Filed"  : "Driver" if not row[4] else "Customer", 
                             "Text"       : row[5]}

        complaints.append(complaint)
    
    db.close()
    return complaints 
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
def WriteNewAdminToDB(form, approving_admin_email):
    db = sqlite3.connect('DB.db3')

    try:
        db.execute(f'''
                        INSERT INTO ADMINS VALUES (
                            (SELECT COUNT(*)+1 FROM ADMINS),
                            '{form['fname']}',
                            '{form['mname']}',
                            '{form['lname']}',
                            '{form['email']}',
                            '{form['phonenum']}',
                            '{sha512(form['pass'].encode()).hexdigest()}',
                            (SELECT Admin_key FROM ADMINS WHERE Email ='{approving_admin_email}')
                        )
                    ''')
        db.commit()
        return 1
    except Exception as e:
       return 0
    finally:
        db.close()

def GetAllAdminsUnderAdmin(email):
    db = sqlite3.connect('DB.db3')

    id = db.execute(f"SELECT Admin_key FROM ADMINS WHERE Email = '{email}'").fetchone()[0]
    data = db.execute(f'''
               with recursive ADMIN_TREE (Admin_key, Fname, Mname, Lname, Email, Phonenum) 
                                AS (
                                    SELECT Admin_key, Fname, Mname, Lname, Email, Phone_num
                                    FROM   ADMINS 
                                    WHERE  Admin_key = {id} 
                                    
                                    UNION ALL
                                    
                                    SELECT A.Admin_key, A.Fname, A.Mname, A.Lname, A.Email, A.Phone_num
                                    FROM   ADMINS as A, ADMIN_TREE as AT
                                    WHERE  A.CREATED_BY = AT.Admin_key
                                )
                                
               SELECT * FROM ADMIN_TREE
                ''')

    data.fetchone()
    
    admins = []
    for row in data:
        admin = {}
        admin['name'] = row[1] + " " + row[2] + " " + row[3]
        admin['Email'] = row[4]
        admin['Phonenum'] = row[5]

        admins.append(admin)
    
    db.close()
    return admins

def RemoveAdmin(email):
    db = sqlite3.connect('DB.db3')

    d = db.execute(f"SELECT Admin_key, CREATED_BY FROM ADMINS WHERE Email = '{email}'").fetchone()

    removed_id, replacement_id = d 

    db.execute(f'''
                UPDATE ADMINS 
                SET CREATED_BY = {replacement_id}

                WHERE CREATED_BY = {removed_id}
                ''')

    db.execute(f"DELETE FROM ADMINS WHERE Admin_key = {removed_id}") 

    
    db.commit()
    db.close()