'''
The JSON-RPC interface to the bitcoind server.
'''
from django.core.exceptions import ObjectDoesNotExist
from jsonrpc import jsonrpc_method
from jsonrpc.decorators import basicauth
from decimal import *

import bitcoind
from bitcoind.proxy import JSONRPCException
from bitcoind.exceptions import _wrap_exception
from bitcoind.connection import BitcoinConnection
from bitcoind.models import Address, DEFAULT_ADDRESS_LABEL
from bitcoind import util
from django.db import connection, transaction
from account.models import MAX_USERNAME_LENGTH

conn = bitcoind.connect_to_local()

@jsonrpc_method('getblockcount')
def getblockcount(request):
    """
    Returns the number of blocks in the longest block chain.
    """
    return conn.getblockcount()

@jsonrpc_method('getblocknumber')
def getblocknumber(request):
    """
    Returns the block number of the latest block in the longest block chain.
    """
    return conn.getblocknumber()

@jsonrpc_method('getconnectioncount')
def getconnectioncount(request):
    """
    Returns the number of connections to other nodes.
    """
    return conn.getconnectioncount()

@jsonrpc_method('getdifficulty')
def getdifficulty(request):
    """
    Returns the proof-of-work difficulty as a multiple of the minimum difficulty.
    """
    return str(conn.getdifficulty())

@jsonrpc_method('getinfo')
def getinfo(request):
    """
    Returns a dictionary containing various state info.
    """
    return conn.getinfo().__dict__

@basicauth()
@jsonrpc_method('getnewaddress')
def getnewaddress(request, label=None):
    """
    Returns a new bitcoin address for receiving payments.
    
    Arguments:

    - *account* -- If account is specified (recommended), it is added to the address book
      so that payments received with the address will be credited to it.

    """
    # Create the label for the address.
    if label is None:
        label = DEFAULT_ADDRESS_LABEL
    
    try:
        # Does this address already exist?
        # If so, we'll just return that object.
        # Note that this query is case-insensitive.
        addressObj = Address.objects.get(user=request.user, label__iexact=label)
    except ObjectDoesNotExist:
        try:
            # Create user's address in bitcoind.
            # Throws an exception if it fails.
            address = conn.getnewaddress(util.getaccount(request.user, label))
            
            # Create the corresponding Address object.
            addressObj = Address(user=request.user, address=address, label=label)
            
            # Does the user have any other addresses?
            # If not, this should be set as their primary.
            if Address.objects.filter(user=request.user).count() == 0:
                addressObj.primary = True
                
            # Save the new address to the database.
            addressObj.save()
        except JSONRPCException, e:
            raise _wrap_exception(e.error)

    return addressObj.address

@basicauth()
@jsonrpc_method('getaccountaddress')
def getaccountaddress(request, label):
    """
    Returns the current bitcoin address for receiving payments to an account.
    
    Arguments:
    
    - *account* -- Account for which the address should be returned.

    """
    # To make sure this isn't redundant
    # with getnewaddress, we'll let
    # this throw an exception if the
    # account does not exist.
    try:
        return conn.getaccountaddress(util.getaccount(request.user, label))
    except JSONRPCException, e:
        raise _wrap_exception(e.error)
    
    return address.address
    

@basicauth()
@jsonrpc_method('setaccount')
def setaccount(request, bitcoinaddress, label):
    """
    Sets the account associated with the given address.
    
    Arguments:

    - *bitcoinaddress* -- Bitcoin address to associate.
    - *account* -- Account to associate the address to.

    """
    # Two use cases here, but only one that
    # we're going to honor.
    # 1) The user provides an address they control
    #    and a new label to give it. In this case
    #    we will simply update the Address object.
    # 2) The user provides a label they control.
    #    The problem here is that they could give
    #    a bitcoin address belonging to someone else
    #    which could lead to confusion when the
    #    address acts like an implicit joint account.
    #    This does, of course, assume the bitcoin
    #    client would let us do that; a likely
    #    possibility since the backend in most cases
    #    will probably be a single bitcoind instance.
    #
    # We're going to ignore use case #2.
    
    # Grab the address object associated with bitcoinaddress.
    try:
        address = Address.objects.get(user=request.user, address=bitcoinaddress)
    except ObjectDoesNotExist, e:
        raise _wrap_exception("You are not the known owner of this address.");
    
    # Make sure there aren't any other addresses trying to
    # use this label. This may not be orthogonal to the
    # bitcoin json-rpc API, but it seems to fit tcatm's
    # js-remote client, which is all we're worried about
    # for this first release.
    if Address.objects.filter(user=request.user, label=label).count() == 0:
        # Throws an exception if it fails.
        result = conn.setaccount(bitcoinaddress, util.getaccount(request.user, label))
        
        # Looks like the update went well on
        # bitcoind's side. Update our db object.
        address.label = label
        address.save()
    else:
        raise _wrap_exception('Address with label already exists!')
    
    return result
    
@basicauth()
@jsonrpc_method('getaccount')
def getaccount(request, bitcoinaddress):
    """
    Returns the account associated with the given address.
    
    Arguments:
    
    - *bitcoinaddress* -- Bitcoin address to get account for.
    """
    # Make sure the user owns the requested account.
    try:
        return Address.objects.get(address=bitcoinaddress, user=request.user).label
    except Exception, e:
        raise _wrap_exception(e)

@basicauth()
@jsonrpc_method('getaddressesbyaccount')
def getaddressesbyaccount(request, label):
    """
    Returns the list of addresses for the given account.
    
    Arguments:
    
    - *account* -- Account to get list of addresses for.
    """ 
    #try:
    #    addresses = self.proxy.getaddressesbyaccount(account) 
    #except JSONRPCException, e:
    #    raise _wrap_exception(e.error)
    return [address.address for address in Address.objects.filter(user=request.user, label=label)]

@basicauth()
@jsonrpc_method('sendtoaddress')
def sendtoaddress(request, bitcoinaddress, amount, comment=None, comment_to=None, minconf=0):
    """
    Sends *amount* from the server's available balance to *bitcoinaddress*.
    
    Arguments:
    
    - *bitcoinaddress* -- Bitcoin address to send to.
    - *amount* -- Amount to send (float, rounded to the nearest 0.01).
    - *comment* -- Comment for transaction.
    - *comment_to* -- Comment for to-address.

    """
    # Set the "toaccount" to None. It will only
    # get set to a value if the user is doing a
    # local transfer.
    toaccount = None
    
    # Get the user's primary bitcoin address.
    fromaddress = Address.objects.get(user=request.user, is_primary=True)
    fromaccount = util.getaccount(request.user, fromaddress.label)
    
    # See if the user is using a username or account indicator to
    # send the bitcoins. If so, resolve the address using that.
    if len(bitcoinaddress) <= MAX_USERNAME_LENGTH or bitcoinaddress.find("+") > -1:
        username, label = util.getusername_and_label(bitcoinaddress)
        toaccount = util.getaccount(username, label)
    
    # See if the address we are sending to exists in our database.
    # If so, use move. If not, use the requested method. 
    if Address.objects.filter(address=bitcoinaddress).count() > 0:
        # Increase the balance of the address we're sending to
        # immediately, since it's on our server.
        toaddress = Address.objects.get(address=bitcoinaddress)
        toaccount = util.getaccount(toaddress.user, toaddress.label)
        
    if toaccount != None:
        # Use the "move" method instead.
        if comment is None:
            return conn.move(fromaccount, toaccount, amount, minconf)
        else:
            return conn.move(fromaccount, toaccount, amount, minconf, comment)
    else:
        # We don't want to actually "sendtoaddress" since that would result in
        # an amount being moved from some unknown account.
        try:
            if comment is None:
                return conn.sendfrom(fromaccount, bitcoinaddress, amount, minconf)
            elif comment_to is None:
                return conn.sendfrom(fromaccount, bitcoinaddress, amount, minconf, comment)
            else:
                return conn.sendfrom(fromaccount, bitcoinaddress, amount, minconf, comment, comment_to)
        except JSONRPCException, e:
            raise _wrap_exception(e.error)

@jsonrpc_method('getreceivedbyaddress')
def getreceivedbyaddress(request, bitcoinaddress, minconf=1):
    """
    Returns the total amount received by a bitcoin address in transactions with at least a
    certain number of confirmations.
    
    Arguments:

    - *bitcoinaddress* -- Address to query for total amount.

    - *minconf* -- Number of confirmations to require, defaults to 1.
    """
    try:
        return conn.getreceivedbyaddress(bitcoinaddress, minconf).__dict__
    except JSONRPCException, e:
        raise _wrap_exception(e.error)
    
@basicauth()
@jsonrpc_method('getreceivedbyaccount')
def getreceivedbyaccount(request, label, minconf=1):
    """
    Returns the total amount received by addresses with an account in transactions with 
    at least a certain number of confirmations.
    
    Arguments:
    
    - *account* -- Account to query for total amount.
    - *minconf* -- Number of confirmations to require, defaults to 1.

    """
    try:
        account = util.getaccount(request.user, label)
        return conn.getreceivedbyaccount(account, minconf).__dict__
    except JSONRPCException, e:
        raise _wrap_exception(e.error)

@basicauth()
@jsonrpc_method('listreceivedbyaddress')
def listreceivedbyaddress(request, minconf=1, includeempty=False):
    """
    Returns a list of addresses.
    
    Each address is represented with a dictionary.

    Arguments:
    
    - *minconf* -- Minimum number of confirmations before payments are included.
    - *includeempty* -- Whether to include addresses that haven't received any payments.

    """
    try:
        addresses = []
        for address in Address.objects.filter(user=request.user):
            amount = conn.getreceivedbyaddress(address.address, minconf=minconf)
            if includeempty or amount > 0:
                addresses.append({"address":address.address, "account":address.label, "amount":amount})
        return addresses
    except JSONRPCException, e:
        raise _wrap_exception(e.error)
    
@basicauth()
@jsonrpc_method('listreceivedbyaccount')
def listreceivedbyaccount(request, minconf=1, includeempty=False):
    """
    Returns a list of accounts.
    
    Each account is represented with a dictionary.
    
    Arguments:
    
    - *minconf* -- Minimum number of confirmations before payments are included.
    
    - *includeempty* -- Whether to include addresses that haven't received any payments.
    """
    try:
        accounts = []
        for address in Address.objects.filter(user=request.user):
            amount = conn.getreceivedbyaccount(address.accountName(), minconf=minconf)
            if includeempty or amount > 0:
                accounts.append({"account":address.label, "amount":amount})
        return accounts
    except JSONRPCException, e:
        raise _wrap_exception(e.error)

@basicauth()
@jsonrpc_method('listaccounts')
def listaccounts(request):
    result = {}
    for address in Address.objects.filter(user=request.user):
        result[address.label] = conn.getbalance(util.getaccount(request.user, address.label))
        
    return result

@basicauth()
@jsonrpc_method('listtransactions')
def listtransactions(request, label, count=10):
    """
    Returns a list of the last transactions for an account.
    
    Each transaction is represented with a dictionary.
    
    Arguments:
    
    - *minconf* -- Minimum number of confirmations before payments are included.
    - *count* -- Number of transactions to return.

    """
    try:
        clean_transactions = []
        if (label == "*"):
            transactions = []
            addresses = Address.objects.filter(user=request.user)
            for address in addresses:
                my_transactions = conn.listtransactions(util.getaccount(request.user, address.label), count)
                transactions.extend(my_transactions)
        else:
            transactions = conn.listtransactions(util.getaccount(request.user, label), count)
            
        for transaction in transactions:
            transaction.account = util.getdisplayname(transaction.account)
            if hasattr(transaction, "otheraccount"):
                transaction.otheraccount = util.getdisplayname(transaction.otheraccount)
                
            clean_transactions.append(transaction.__dict__)
        return clean_transactions
    except JSONRPCException, e:
        raise _wrap_exception(e.error)

@jsonrpc_method('validateaddress')
def validateaddress(request, validateaddress):
    """
    Validate a bitcoin address and return information for it.

    The information is represented by a dictionary.
    
    Arguments:
    
    - *validateaddress* -- Address to validate.

    """
    try:
        return conn.validateaddress(validateaddress).__dict__
    except JSONRPCException, e:
        raise _wrap_exception(e.error)
    
@basicauth()
@jsonrpc_method('getbalance')
def getbalance(request, label=None, minconf=0):
    """
    Get the current balance, either for an account or the total server balance.
    
    Arguments:
    - *account* -- If this parameter is specified, returns the balance in the account.

    """
    try:
        return str(conn.getbalance(util.getaccount(request.user, label)))
    except JSONRPCException, e:
        raise _wrap_exception(e.error)
    
@basicauth()
@jsonrpc_method('move')
def move(request, fromlabel, toaccount, amount, minconf=1, comment=None):
    """
    Move from one account in your wallet to another.
    
    Arguments:
    
    - *fromaccount* -- Source account name.
    - *toaccount* -- Destination account name.
    - *amount* -- Amount to transfer.
    - *minconf* -- Minimum number of confirmations required for transferred balance.
    - *comment* -- Comment to add to transaction log.
    
    """
    try:
        # Make sure the requested accounts exist.
        fromaccount = util.getaccount(request.user, fromlabel)
        try:
            fromaddress = Address.objects.get(user=request.user, label=fromlabel)
        except ObjectDoesNotExist:
            raise _wrap_exception("Could not find account \"%s\"" % fromlabel)
        
        username, tolabel = util.getusername_and_label(toaccount)
        
        if comment is None:
            return conn.move(fromaccount, toaccount, amount, minconf)
        else:
            return conn.move(fromaccount, toaccount, amount, minconf, comment)
    except JSONRPCException, e:
        raise _wrap_exception(e.error)

@basicauth()
@jsonrpc_method('sendfrom')
def sendfrom(request, fromlabel, tobitcoinaddress, amount, minconf=1, comment=None, comment_to=None):
    """
    Sends amount from account's balance to bitcoinaddress. This method will fail 
    if there is less than amount bitcoins with minconf confirmations in the account's 
    balance (unless account is the empty-string-named default account; it 
    behaves like the sendtoaddress method). Returns transaction ID on success.
    
    Arguments:
    
    - *fromaccount* -- Account to send from.
    - *tobitcoinaddress* -- Bitcoin address to send to.
    - *amount* -- Amount to send (float, rounded to the nearest 0.01).
    - *minconf* -- Minimum number of confirmations required for transferred balance.
    - *comment* -- Comment for transaction.
    - *comment_to* -- Comment for to-address.

    """ 
    # See if the address we are sending to exists in our database.
    # If so, use move. If not, use the requested method. 
    if Address.objects.filter(address=bitcoinaddress).count() > 0:
        # Increase the balance of the address we're sending to
        # immediately, since it's on our server.
        toaddress = Address.objects.get(address=bitcoinaddress)
        toaccount = util.getaccount(toaddress.user, toaddress.label)
        fromaccount = util.getaccount(request.user, fromlabel)
        
        # Use the "move" method instead.
        if comment is None:
            return conn.move(fromaccount, toaccount, amount, minconf)
        else:
            return conn.move(fromaccount, toaccount, amount, minconf, comment)
    else:
        try:
            if comment is None:
                return conn.sendfrom(fromaccount, tobitcoinaddress, amount, minconf)
            elif comment_to is None:
                return conn.sendfrom(fromaccount, tobitcoinaddress, amount, minconf, comment)
            else:
                return conn.sendfrom(fromaccount, tobitcoinaddress, amount, minconf, comment, comment_to)
        except JSONRPCException, e:
            raise _wrap_exception(e.error)
