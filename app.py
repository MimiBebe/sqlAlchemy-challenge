import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt
import dateutil.relativedelta as relativedelta

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station



#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# main/index page
@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Weather API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start"
        f"/api/v1.0/start/end<br/>"
    )

#  /api/v1.0/precipitation
# Convert the query results to a dictionary using `date` as the key and `prcp` as the value.
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all passenger names"""
    # Query all passengers
    prcpData = session.query(Measurement.date,Measurement.prcp).order_by(Measurement.date.desc()).all()

    session.close()

    prcpList= []
    for date, prcp in prcpData:
        prcpDict = {}
        prcpDict[date] = prcp
        prcpList.append(prcpDict)

    return jsonify(prcpList)

# /api/v1.0/stations
# Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    stationQuery = session.query(Station.name.distinct()).all()
    session.close()

    allStations= list(np.ravel(stationQuery))
    stationDict = {"stations":allStations} 

    return jsonify(stationDict)

# /api/v1.0/tobs
# Query the dates and temperature observations of the most active station for the last year of data.
# Return a JSON list of temperature observations (TOBS) for the previous year.

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    # get the most active station
    mostActiveStationIdQuery = session.query(Measurement.station).group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()

    # get the latest date in hawaii.sqlite
    latestData = session.query(Measurement).order_by(Measurement.date.desc()).first()

    # get the date 12 months from latest date
    # Calculate the date 1 year ago from the last data point in the database
    toDate = dt.datetime.strptime(latestData.date, '%Y-%m-%d')
    fromDate = toDate - relativedelta.relativedelta(months=12) 

    # Get 1 year temps for most active station
    mostActiveStationOneYearData = session.query(Measurement.date, Measurement.tobs)\
    .filter(Measurement.station == mostActiveStationIdQuery[0]).filter(Measurement.date >= fromDate).all()    

    session.close()

    # return json dict 
    tobsList= []
    for date, tobs in mostActiveStationOneYearData:
        tobsDict = {}
        tobsDict[date] = tobs
        tobsList.append(tobsDict)

    return jsonify(tobsList)

# /api/v1.0/<start>
# When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.
# Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start
@app.route("/api/v1.0/<start>")
def startDateStats(start):
    # format of date yyyy-mm-dd
    
    return start


# /api/v1.0/<start>/<end>
# When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date
# Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
@app.route("/api/v1.0/<start>/<end>")
def startEndDateStats(start,end):
    # format of date yyyy-mm-dd
    
    return f"From {start} To {end}"

#################################################
# Flask Run
#################################################
if __name__ == "__main__":
    app.run(debug=True)