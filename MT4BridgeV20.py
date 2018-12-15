import json
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
from oandapyV20.exceptions import V20Error
import functions as bridge
import time, datetime
import static

accountID = static.short_account_id
access_token = static.token

if (static.live_trading):
    client = oandapyV20.API(access_token=access_token, environment='live')
else:
    client = oandapyV20.API(access_token=access_token, environment='practice')

bridge.update_account()
bridge.update_positions()

alive_timer = 60

while True:

    if (datetime.datetime.now().second % alive_timer == 0): bridge.alive_check()
    bridge.close_positions()
    bridge.open_trades()

    time.sleep(1)

'''
r = accounts.AccountDetails(accountID=accountID)
try:
    rv = client.request(r)
except V20Error as err:
    print("V20Error occurred: {}".format(err))
else:
    print("Response: {}\n{}".format(r.status_code, json.dumps(rv, indent=2)))
print(json.dumps(response, indent=2))

'''