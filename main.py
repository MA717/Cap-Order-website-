
from flask import Flask, render_template, request, redirect, url_for, make_response
import DB
from helper import *
app = Flask(__name__)

@app.route("/", methods = ["GET","POST"])
@app.route("/home", methods = ["GET","POST"])
def home():
    #A submit
    if  request.method == "POST":
        #Handling sign up
        if "SignUpCustomer" in request.form:
            if(DB.WriteCustomerToDB(request.form)):
                 res = make_response(render_template("index.html"))
                 res.set_cookie(f"ALADDINCUSTOMER{request.form['Email']}", request.form['Password'] )
                 return res
            else:
                pass
        elif "SignUpDriver" in request.form: 
            if(DB.WriteDriverToDB(request.form)):
                 res = make_response(render_template("index.html"))
                 res.set_cookie(f"ALADDINDRIVER{request.form['Email']}", request.form['Password'] )
                 return res
            else:
                pass
        #Login
        else:
            if "SignCustomer" in request.form:
                user = DB.UserExists(request.form['email'], request.form['pass'],"CUSTOMERS")
                if( (user is not None) and (user != -1) ):
                    res = make_response(render_template('WaypointCus.html', email = request.form['email']))
                    res.set_cookie(f"ALADDINCUSTOMER{request.form['email']}", request.form['pass'])
                    return res
            else:
                user = DB.UserExists(request.form['email'], request.form['pass'],"DRIVERS")
                if( (user is not None) and (user != -1) ):
                    res = make_response(render_template('WaypointDriv.html', email = request.form['email']))
                    res.set_cookie(f"ALADDINDRIVER{request.form['email']}", request.form['pass'])
                    return res
    
    #First request
    return render_template("index.html")

@app.route("/Customer<email>/", methods = ["GET","POST"])
def customer(email):
    #Authentication
    user_name  = DB.UserExists(email, request.cookies.get(f"ALADDINCUSTOMER{email}"), "CUSTOMERS")
    if(not user_name) : return render_template("NonExistentUser.html")
    if(user_name == -1): return render_template("NonExistentUser.html")

    if  request.method == "POST":
        if "SubmitTrip" in request.form:
            DB.WriteTripRequestToDB(request.form, email)

        elif "VIEW_OFFER" in request.form:
            return render_template("ViewOffersCust.html", date = request.form['Trip_date'], offers = DB.GetAllOffersForTripCustomer(request.form))
        
        elif "ACCEPT_OFFER" in request.form:
            DB.ChangeOfferStatus(email,request.form['trip_date'],request.form['driver_email'])

        elif "RATING" in request.form:
            DB.AddOrUpdateRatingByCustomer(request.form)
        else:
            DB.WriteTripComplaintByCustomer(request.form)
            
    #GET request
    CitytoDistricts, DistrictToStreets = mapCityToDistricts_DistrictToStreets(DB.GetLocations())
    trip_requests,confirmed_trips = DB.GetAllTripsForUser(email)
    return render_template("Customer.html", 
                            customer_name     = user_name,
                            email             = email, 
                            CitytoDistricts   = CitytoDistricts, 
                            DistrictToStreets = DistrictToStreets,
                            trip_requests     = trip_requests, 
                            confirmed_trips   = confirmed_trips)

@app.route("/Driver<email>/", methods = ["GET","POST"])
def driver(email):
    user_name  = DB.UserExists(email, request.cookies.get(f"ALADDINDRIVER{email}"), "DRIVERS")
    if(not user_name) :  return render_template("NonExistentUser.html")
    if(user_name == -1): return render_template("NonExistentUser.html")

    return render_template("driver.html", name = user_name, email = str(email))

@app.route('/availt<email>/', methods = ["GET","POST"])
def available_trips(email):
    if request.method == "POST":
        if request.form['TYPE'] == "OFFER":
            DB.WriteTripOfferToDB(request.form)
        
    trips = DB.GetAllAvailableTripsForDriver(email) 
    return render_template("ViewTrips.html", trips = trips , email = str(email))

@app.route('/dconft<email>/', methods = ["GET","POST"])
def driver_confirmed_trips(email):
    if request.method == "POST":
        if "RATING" in request.form:
            DB.AddOrUpdateRatingByDriver(request.form)
        else:
            DB.WriteTripComplaintByDriver(request.form)

    trips = DB.GetAllConfirmedTripsDriver(email)
    return render_template("Viewdriverpast.html", email = email, trips = trips)

@app.route('/doffers<email>/', methods = ["GET","POST"])
def driver_offers(email):
    if request.method == "POST":
        DB.ConfrimAcceptedOffer(email, request.form['Customer_email'], request.form['Trip_date'])

    return render_template("ViewOffersDriv.html", offers = DB.GetAllOffersMadeByDriver(email))

@app.route('/ChPfr<type>/<email>/', methods = ["GET","POST"])
def change_pass(type,email):
    if request.method == "POST":
        if( DB.ChangePasswordOfUser(request.form['Old_Pass'],
                                 request.form['New_Pass'],
                                 type,
                                 email) != -1):
            if type == "CUSTOMERS" or type == "DRIVERS":
                res = make_response(render_template(
                                                f'''Waypoint{'Cus' if type == 'CUSTOMERS' else 'Driv'}.html''',
                                                email = email))

                res.set_cookie(f"ALADDIN{type[:-1]}{email}", request.form['New_Pass'] )
            
                return res
            else:
                res = make_response(render_template(f"WayPointEmpl.html", type = type, email = email))

                if type == "SUPPORT" : type += "s"
                res.set_cookie(f"ALADDIN{type[:-1]}{email}", request.form['New_Pass'])
                return res

        else: return render_template("NonExistentUser.html")
            
    
    return render_template("ChangePassword.html")

@app.route('/Admin<email>/', methods = ["GET","POST"])
def admin(email):
    user_name  = DB.UserExists(email, request.cookies.get(f"ALADDINADMIN{email}"), "ADMINS")
    if(not user_name) :  return render_template("NonExistentEmployee.html")
    if(user_name == -1): return render_template("NonLoggedEmployee.html")
   

    return render_template("Admin.html", email = email)


@app.route('/vaccppdeladm<email>/', methods = ["GET","POST"])
def view_create_delete_admins(email):
    if request.method == "POST":
        if "CreateAdm" in request.form:
            DB.WriteNewAdminToDB(request.form, email )
        else:
            DB.RemoveAdmin(request.form['Email'])
    
    return render_template("ViewAdmin.html", admins = DB.GetAllAdminsUnderAdmin(email))

@app.route('/AladdinEmps/', methods = ["GET","POST"])
def aladdin_employees():
    if request.method == "POST":
        #New employee SignUp 
        if "SignUpMan" in request.form or "SignUpSupp" in request.form:
            DB.WriteNewEmployeeToDB(request.form)
        #Sign in
        else:
            type = "SUPPORT" if "SignInSupp" in request.form else "ADMINS"  if "SignInAdm"  in request.form else "MANAGERS"
            user_name = DB.UserExists(request.form['Email'], request.form['Password'], type)
            if user_name is not None and user_name != -1:
                res = make_response(render_template(f"WayPointEmpl.html", type = type, email = request.form['Email']))

                if type == "SUPPORT" : type += "s"
                res.set_cookie(f"ALADDIN{type[:-1]}{request.form['Email']}", request.form['Password'])
                return res

    return render_template("myWorker.html")

@app.route('/Support<email>/', methods = ["GET","POST"])
def alaadin_support(email):
    user_name  = DB.UserExists(email, request.cookies.get(f"ALADDINSUPPORT{email}"), "SUPPORT")
    if(not user_name) :  return render_template("NonExistentEmployee.html")
    if(user_name == -1): return render_template("NonLoggedEmployee.html")
    
    if request.method == "POST":
        DB.MarkComplaintSolved(request.form)

    return render_template("Support.html", email = email, complaints = DB.GetAllUnresolvedComplaintsForSupport(email))

@app.route('/Manager<email>/', methods = ["GET","POST"])
def alaadin_manager(email):
    user_name  = DB.UserExists(email, request.cookies.get(f"ALADDINMANAGER{email}"), "MANAGERS")
    if(not user_name) :  return render_template("NonExistentEmployee.html")
    if(user_name == -1): return render_template("NonLoggedEmployee.html")
    
    return render_template("Manager.html", email = email)

@app.route('/urcoms<email>/', methods  = ["GET","POST"])
def unresolved_complaints(email):
    if request.method == "POST":
        DB.AssignComplaintToSupport(request.form['Email'], request.form)
    
    return render_template("ViewAllComplaints.html", complaints = DB.GetAllUnresolvedComplaintsForSupport())

@app.route('/Nwmng<email>/', methods = ["GET","POST"])
def new_managers(email):
    if request.method == "POST":
        DB.AcceptApplyingManager(request.form['Email'],email)
    
    return render_template("ViewNewManeger.html", applying_managers = DB.GetAllApplyingManagers())

@app.route('/NwsuPP<email>/', methods = ["GET","POST"])
def new_support(email):
    if request.method == "POST":
        DB.AcceptApplyingSupport(request.form['Email'],email)
    
    return render_template("ViewNewSpportEmployee.html", applying_support = DB.GetAllApplyingSupport())

@app.route('/mngsumng<email>/', methods = ["GET","POST"])
def managers_under_manager(email):
    if request.method == "POST":
        DB.FireEmployee(request.form['Email'], "MANAGERS")
    
    return render_template("ViewManeger.html", managers = DB.GetAllManagersUnderManager(email))

@app.route('/suppUmngS<email>/', methods = ["GET","POST"])
def support_under_manager(email):
    if request.method == "POST":
        DB.FireEmployee(request.form['Email'], "SUPPORT")
    
    return render_template("ViewSupport.html", support = DB.GetAllSupportsUnderManager(email))

if(__name__ == '__main__'): app.run(debug = True)