import os
import json
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest
from oandapyV20.contrib.requests import TakeProfitDetails, StopLossDetails
from oandapyV20.exceptions import V20Error
from datetime import datetime, timedelta
import static

CLOSE_POSITION_MESSAGE = '''POSITION CLOSED:  ===============================
                  Time: {time} EST
                  Pair: {instrument}
                  Units: {units} ({direction})
                  P/L: ${pl}
                  ==============================='''
CLOSE_PARTIAL_MESSAGE = '''PARTIAL CLOSE:  ===============================
                  Time: {time} EST
                  Pair: {instrument}
                  Units: {units} ({direction})
                  P/L: ${pl}
                  ==============================='''
OPEN_POSITION_MESSAGE = '''POSITION OPENED:  ===============================
                  Time: {time} EST
                  Pair: {instrument}
                  Units: {units} ({direction})
                  Stoploss: {sl}
                  Takeprofit: {tp}
                  ==============================='''
#######################################################
# create a lock file to prevent mt4 from accessing data
#######################################################
def create_lock_file():
    try:
        file = open(static.filepath+"bridge_lock","w")
        file.close()
    except Exception as e:
        print(e)
    return

############################
# delete the above lock file
############################
def delete_lock_file():
    try:
        if os.path.isfile(static.filepath+"bridge_lock"):
            os.remove(static.filepath+"bridge_lock")
    except Exception as e:
        print(e)
    return

#######################################
# close all positions for an instrument
#######################################
def close_positions():
    if not is_directory_locked():
        try:
            for fn in os.listdir(static.filepath): # loop through files in directory
                if 'close-' in fn:
                    create_lock_file()
                    cmd,instrument,side,numUnits = fn.split('-')

                    if (numUnits == '0'):
                        numUnits = "ALL"

                    if (static.live_trading):
                        client = oandapyV20.API(static.token, environment='live')
                    else:
                        client = oandapyV20.API(static.token, environment='practice')

                    if (side == "buy"):
                    	#close long positions
                    	r = positions.PositionClose(static.long_account_id, instrument, {"longUnits": numUnits})
                    	try:
                            client.request(r)
                            pl = '{:,.2f}'.format(float(r.response["longOrderFillTransaction"]["pl"]))
                            units = abs(int(r.response["longOrderFillTransaction"]["units"]))
                            time = (datetime.now() + timedelta(hours = 3)).strftime('%m/%d/%Y @ %I:%M %p')
                            if (numUnits == "ALL"):
                                print(CLOSE_POSITION_MESSAGE.format(time=time, instrument=instrument, direction = 'long', units=units, pl=pl))
                            else:
                                print(CLOSE_PARTIAL_MESSAGE.format(time=time, instrument=instrument, direction = 'long', units=units, pl=pl))
                    	except V20Error as err:
                            pass

                    if (side == "sell"):
                    	#close short positions
                    	r = positions.PositionClose(static.short_account_id, instrument, {"shortUnits": numUnits})
                    	try:
                            client.request(r)
                            pl = '{:,.2f}'.format(float(r.response["shortOrderFillTransaction"]["pl"]))
                            units = abs(int(r.response["shortOrderFillTransaction"]["units"]))
                            time = (datetime.now() + timedelta(hours = 3)).strftime('%m/%d/%Y @ %I:%M %p')
                            if (numUnits == "ALL"):
                                print(CLOSE_POSITION_MESSAGE.format(time=time, instrument=instrument, direction = 'short', units=units, pl=pl))
                            else:
                                print(CLOSE_PARTIAL_MESSAGE.format(time=time, instrument=instrument, direction = 'short', units=units, pl=pl))
                    	except V20Error as err:
                            pass

                    # delete file
                    if os.path.isfile(static.filepath+fn):
                        os.remove(static.filepath+fn)

                    # delete minmax file
                    if os.path.isfile(static.filepath+'minmax-'+instrument+'.txt'):
                        os.remove(static.filepath+'minmax-'+instrument+'.txt')

                    # delete stoploss file
                    if os.path.isfile(static.filepath+'stoploss-'+instrument+'.txt'):
                        os.remove(static.filepath+'stoploss-'+instrument+'.txt')

                    # delete entry file
                    if os.path.isfile(static.filepath+'entry-'+instrument+'.txt'):
                        os.remove(static.filepath+'entry-'+instrument+'.txt')

                    # delete target file
                    if os.path.isfile(static.filepath+'target-'+instrument+'.txt'):
                        os.remove(static.filepath+'target-'+instrument+'.txt')

                    update_positions()
                    update_account()
                    delete_lock_file()

        except Exception as e:
            print(e)
    return

###################
# open market order
###################
def open_trades():
    if not is_directory_locked():
        try:
           for fn in os.listdir(static.filepath): # loop through files in directory
               if 'openmarket-' in fn:
                    create_lock_file()
                    cmd,pair,side,size,stoploss,takeprofit = fn.split('-')

                    stoploss = float(stoploss)
                    takeprofit = float(takeprofit)
                    size = int(size)

                    if (side == "sell"):
                        size = str(size * -1)

                    if (stoploss > 0 and takeprofit > 0):
                        mktOrder = MarketOrderRequest(
                            instrument = str(pair),
                            units = size,
                            takeProfitOnFill=TakeProfitDetails(price=takeprofit).data,
                            stopLossOnFill=StopLossDetails(price=stoploss).data)
                    elif (stoploss > 0):
                        mktOrder = MarketOrderRequest(
                            instrument = str(pair),
                            units = size,
                            stopLossOnFill=StopLossDetails(price=stoploss).data)
                    else:
                        mktOrder = MarketOrderRequest(
                            instrument = str(pair),
                            units = size)

                    if (static.live_trading):
                        client = oandapyV20.API(static.token, environment='live')
                    else:
                        client = oandapyV20.API(static.token, environment='practice')
                    if (side == "sell"):
                        r = orders.OrderCreate(static.short_account_id,data=mktOrder.data)
                    else:
                        r = orders.OrderCreate(static.long_account_id,data=mktOrder.data)

                    try:
                        rv = client.request(r)
                        if (stoploss == 0):
                            stop = "none"
                        else:
                            stop = stoploss
                        if (takeprofit == 0):
                            profit = "none"
                        else:
                            profit = takeprofit
                        rawUnits = int(r.response["orderFillTransaction"]["units"])
                        if (rawUnits < 0):
                            direction = 'short'
                        else:
                            direction = 'long'
                        units = abs(rawUnits)
                        time = (datetime.now() + timedelta(hours = 3)).strftime('%m/%d/%Y @ %I:%M %p')
                        print(OPEN_POSITION_MESSAGE.format(time=time, instrument=pair, direction=direction, units=units, sl=stop, tp=profit))
                    except V20Error as err:
                        print("V20Error occurred: {}".format(err))

                    # delete file
                    if os.path.isfile(static.filepath+fn):
                        os.remove(static.filepath+fn)

                    # update positions
                    update_positions()
                    update_account()
                    delete_lock_file()
        except Exception as e:
            print(e)
    return

######################
# update all positions
######################
def update_positions():

    if not is_directory_locked():
        create_lock_file()
        try:
            # delete all current positions prior to update
            for fn in os.listdir(static.filepath): # loop through files in directory
                if 'position-' in fn:
                    os.remove(static.filepath+fn)

            if (static.live_trading):
                client = oandapyV20.API(static.token, environment='live')
            else:
                client = oandapyV20.API(static.token, environment='practice')

            # update short positions
            response = positions.OpenPositions(static.short_account_id)
            rv = client.request(response)
            
            #print(rv["positions"])

            for position in rv["positions"]:
                longunits = int(position["long"]["units"])
                shortunits = int(position["short"]["units"]) * -1
                
                if(longunits > 0):
                    side = "buy"
                    units = position["long"]["units"]
                    avgPrice = position["long"]["averagePrice"]
                    total = len(position["long"]["tradeIDs"])
                if(shortunits > 0):
                    side = "sell"
                    units = abs(int(position["short"]["units"]))
                    avgPrice = position["short"]["averagePrice"]
                    total = len(position["short"]["tradeIDs"])
                # create file position-EUR_USD-buy-2500-1.13041
                file = open(static.filepath+"position-"+position.get("instrument")+"-short.txt","w")
                file.write(side+","+
                           str(units)+","+
                           str(avgPrice)+","+
                           str(total))
                file.close()

            # update long positions
            response = positions.OpenPositions(static.long_account_id)
            rv = client.request(response)
            
            #print(rv["positions"])

            for position in rv["positions"]:
                longunits = int(position["long"]["units"])
                shortunits = int(position["short"]["units"]) * -1
                
                if(longunits > 0):
                    side = "buy"
                    units = position["long"]["units"]
                    avgPrice = position["long"]["averagePrice"]
                    total = len(position["long"]["tradeIDs"])
                if(shortunits > 0):
                    side = "sell"
                    units = abs(int(position["short"]["units"]))
                    avgPrice = position["short"]["averagePrice"]
                    total = len(position["short"]["tradeIDs"])
                # create file position-EUR_USD-buy-2500-1.13041
                file = open(static.filepath+"position-"+position.get("instrument")+"-long.txt","w")
                file.write(side+","+
                           str(units)+","+
                           str(avgPrice)+","+
                           str(total))
                file.close()

            print("UPDATE POSITIONS: Success")
        except Exception as e:
            print(e)
        delete_lock_file()
    return

########################
# update account details
########################
def update_account():

    if not is_directory_locked():
        create_lock_file()

        if (static.live_trading):
            client = oandapyV20.API(static.token, environment='live')
        else:
            client = oandapyV20.API(static.token, environment='practice')        

        # update short account
        response = accounts.AccountDetails(static.short_account_id)

        try:
            rv = client.request(response)

            file = open(static.filepath+"account-short.txt","w")
            file.write(str(rv["account"]["balance"])+","+
                       str(rv["account"]["openTradeCount"])+","+
                       str(rv["account"]["marginAvailable"])+","+
                       str(rv["account"]["marginUsed"])+","+
                       str(rv["account"]["pl"])
                       )
            file.close()
        except V20Error as err:
            print("V20Error occurred: {}".format(err))

        # update long account
        response = accounts.AccountDetails(static.long_account_id)

        try:
            rv = client.request(response)

            file = open(static.filepath+"account-long.txt","w")
            file.write(str(rv["account"]["balance"])+","+
                       str(rv["account"]["openTradeCount"])+","+
                       str(rv["account"]["marginAvailable"])+","+
                       str(rv["account"]["marginUsed"])+","+
                       str(rv["account"]["pl"])
                       )
            file.close()

            print("UPDATE ACCOUNT:   Success")
        except V20Error as err:
            print("V20Error occurred: {}".format(err))
        delete_lock_file()

    return

#############################
# is directory locked by MT4?
#############################
def is_directory_locked():
    locked = False
    try:
        if os.path.isfile(static.filepath+'MT4-Locked'):
            locked = True
    except Exception as e:
        print(e)
    return locked
