import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func,and_

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
        f"/api/v1.0/start<br/>"
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

    # format of date yyyymmdd
    if len(start)==8:
        startDate = dt.date(year=int(start[0:4]), month=int(start[4:6]), day=int(start[6:8]))
     
        # calculate `TMIN`, `TAVG`, and `TMAX` for  all dates greater than and equal to the start date
        session = Session(engine)
        startDateQuery = session.query(func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs))\
        .filter(Measurement.date >= startDate).all()    
        session.close()

        # startDateQuery should only have 1 row
        startDateStatsDict ={}
        startDateStatsDict["TMIN"] = startDateQuery[0][0]
        startDateStatsDict["TAVG"] = startDateQuery[0][1]
        startDateStatsDict["TMAX"] = startDateQuery[0][2]

        return jsonify(startDateStatsDict)

    return jsonify({"error": f"Invalid date entry {start} . Please enter a valid date: yyyymmdd"}), 404


# /api/v1.0/<start>/<end>
# When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for start-end range.
# Return a JSON list of the minimum temperature, the average temperature, and the max temperature for start-end range.
@app.route("/api/v1.0/<start>/<end>")
def startEndDateStats(start,end):
    # format of date yyyy-mm-dd

    if len(start)==8 and len(end)==8:
        startDate = dt.date(year=int(start[0:4]), month=int(start[4:6]), day=int(start[6:8]))
        endDate = dt.date(year=int(end[0:4]), month=int(end[4:6]), day=int(end[6:8]))
        # calculate `TMIN`, `TAVG`, and `TMAX` for  all dates greater than and equal to the start date and smaller than end date
        session = Session(engine)
        startEndDateQuery = session.query(func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs))\
        .filter(and_(Measurement.date >= startDate,Measurement.date <= endDate)).all()    
        session.close()

        # startEndDateQuery should only have 1 row
        startEndDateStatsDict ={}
        startEndDateStatsDict["TMIN"] = startEndDateQuery[0][0]
        startEndDateStatsDict["TAVG"] = startEndDateQuery[0][1]
        startEndDateStatsDict["TMAX"] = startEndDateQuery[0][2]

        return jsonify(startEndDateStatsDict)

    return jsonify({"error": f"Invalid date entry/entries {start} and/or {end} . Please enter valid dates: yyyymmdd"}), 404

    



#################################################
# Flask Run
#################################################
if __name__ == "__main__":
    app.run(debug=True)