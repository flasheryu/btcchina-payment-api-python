#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import time
import re
import hmac
import hashlib
import base64
import httplib
import json
 
class BTCChina():
    def __init__(self,access=None,secret=None):
        self.access_key=access
        self.secret_key=secret
        self.conn=httplib.HTTPSConnection("api.btcchina.com")
 
    def _get_tonce(self):
        return int(time.time()*1000000)
 
    def _get_params_hash(self,pdict):
        pstring=""
        # The order of params is critical for calculating a correct hash
        fields=['tonce','accesskey','requestmethod','id','method','params']
        for f in fields:
            if pdict[f]:
                if f == 'params':
                    # Convert list to string, then strip brackets and spaces
                    # probably a cleaner way to do this
 
                    param_string=str(pdict[f]);
                    # Replace None with empty string
 
                    param_string=param_string.replace('None', '')
 
                    param_string=re.sub("[\[\] ]","",param_string)
                    param_string=re.sub("'",'',param_string)
                    pstring+=f+'='+param_string+'&'
                else:
                    pstring+=f+'='+str(pdict[f])+'&'
            else:
                pstring+=f+'=&'
        pstring=pstring.strip('&')
        print pstring
 
        # now with correctly ordered param string, calculate hash
        phash = hmac.new(self.secret_key, pstring, hashlib.sha1).hexdigest()
 
        return phash
 
    def _private_request(self,post_data):
        #fill in common post_data parameters
        tonce=self._get_tonce()
        post_data['tonce']=tonce
        post_data['accesskey']=self.access_key
        post_data['requestmethod']='post'
 
        # If ID is not passed as a key of post_data, just use tonce
        if not 'id' in post_data:
            post_data['id']=tonce
 
        pd_hash=self._get_params_hash(post_data)
 
        # must use b64 encode        
        auth_string='Basic '+base64.b64encode(self.access_key+':'+pd_hash)
        headers={'Authorization':auth_string,'Json-Rpc-Tonce':tonce}
 
        #post_data dictionary passed as JSON        
        self.conn.request("POST",'/api.php/payment',json.dumps(post_data),headers)
        response = self.conn.getresponse()
 
        # check response code, ID, and existence of 'result' or 'error'
        # before passing a dict of results
        if response.status == 200:
            # this might fail if non-json data is returned
            resp_dict = json.loads(response.read())
 
            # The id's may need to be used by the calling application,
            # but for now, check and discard from the return dict
            if str(resp_dict['id']) == str(post_data['id']):
                if 'result' in resp_dict:
                    return resp_dict['result']
                elif 'error' in resp_dict:
                    return resp_dict['error']
        else:
            # not great error handling....
            print "status:",response.status
            print "reason:",response.reason
 
        return None

    def create_purchase_order(self, price, currency, notificationURL, 
                              returnURL = None, externalKey = None, itemDesc = None,
                              phoneNumber = None, settlementType = 0, post_data = {}):
        post_data['method'] = 'createPurchaseOrder'
        post_data['params'] = [price, currency, notificationURL, returnURL,
                               externalKey, itemDesc, phoneNumber, settlementType]
        return self._private_request(post_data)

    def get_purchase_order(self, order_id, post_data = {}):
        post_data['method'] = 'getPurchaseOrder'
        post_data['params'] = [order_id]
        return self._private_request(post_data)

    def get_purchase_orders(self, limit = None, offset = 0, 
                            fromDate = None, toDate = None, status = None, externalKey = None, 
                            post_data = {}):
        post_data['method'] = 'getPurchaseOrders'
        post_data['params'] = [limit, offset, fromDate, toDate, status, externalKey]
        return self._private_request(post_data)
