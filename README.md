# MT4 to FXTrade V20 Bridge - Dual Account for Artificial Hedging

This is a modification of my original MT4 to FXTrade V20 Bride to allow for using one account to place short trades and a second account to place long trades.  Doing this allows for a form of hedging, although you would need to transfer funds between accounts on a regular basis to keep things balanced.

This Python script to act as a bridge from MT4 to Oanda FXtrade. I use this to allow my MT4 expert advisors to send trades to Oanda's FXtrade V20 API. Using this I can place trades as small as 1 unit.

The MQL script writes files to the files/FXtrade folder and this Python script reads them and manipulates orders via the Oanda API. Reading and writing files to communicate orders was the most consistent method that I found to get data from MT4 to Python. It is also unlikely that a future MT4 update will disable file usage.

### Requirements
---
[oandapyV20](https://github.com/hootnot/oanda-api-v20)

requests

six

### Configuration
---
Create a folder named FXtrade within the /MQL4/Files directory of your MT4 installation.  Edit the details within the static.py file using your Oanda connection details and the directory path to the FXtrade folder you just created.

### Trade Functions
---
I do not use pending orders but rather allow my experts to monitor when to open and close trades, so the functionality is limited to the following.

+ Open market order with/without stoploss and target
+ Add on to existing trade
+ Fully or partially close trade

---

```
// create order file
bool OpenMarketOrder(string fuInstrument, string fuSide, int fuUnits, double fuStop=0.0, double fuTarget=0.0){
   int fuFilehandle;
   bool fuOrder;
   string pair = fuInstrument;
   StringReplace(pair,"_","");
   
   string fuCommand = "openmarket-"+fuInstrument+"-"+fuSide+"-"+IntegerToString(fuUnits)+"-"+DoubleToStr(fuStop,int(MarketInfo(pair,MODE_DIGITS)))+"-"+DoubleToStr(fuTarget,int(MarketInfo(pair,MODE_DIGITS)));

   LockDirectory();
   fuFilehandle=FileOpen("FXtrade\\"+fuCommand,FILE_WRITE|FILE_TXT);
   if(fuFilehandle!=INVALID_HANDLE){
      FileClose(fuFilehandle);
      fuOrder = True;
   } else fuOrder = False;
   UnlockDirectory();
   Sleep(5000);
   return fuOrder;
}

// create close position file
bool ClosePosition(string fuInstrument, int arrID, string fuSide, int fuUnits=0){
   
   string pair = fuInstrument;
   StringReplace(pair,"_","");

   int fuFilehandle;
   fuFilehandle=FileOpen("FXtrade\\close-"+fuInstrument+"-"+fuSide+"-"+IntegerToString(fuUnits),FILE_WRITE|FILE_TXT);
   if(fuFilehandle!=INVALID_HANDLE){
      FileClose(fuFilehandle);
      SendNotification("Close "+pair+": "+DoubleToStr(PairInfo[arrID].Profit,2));
      return True;
   } else return False;
}

// lock directory so python does not access files
bool LockDirectory(){
   int fuFilehandle;
   fuFilehandle=FileOpen("FXtrade\\MT4-Locked",FILE_WRITE|FILE_TXT);
   if(fuFilehandle!=INVALID_HANDLE){
      FileClose(fuFilehandle);
      return True;
   } else return False;
}

// unlock directory so python can access files
bool UnlockDirectory(){
   int fuFilehandle;
   fuFilehandle=FileDelete("FXtrade\\MT4-Locked");
   if (fuFilehandle == False) return False;
      else return True;
}
```