import os
from eth_account import Account
from web3 import Web3
import json
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware

# TODO make env variable
PM_ABI = "/home/ubuntu2/projects/4tr-solidity/build/contracts/PredictionManager.json"
PF_ABI = "/home/ubuntu2/projects/4tr-solidity/build/contracts/PriceFeedManager.json"

PM_ADDRESS = "0xE2c6b4A06ed3B1701A1441BEA673Ee2d0DDE46b1"
PF_ADDRESS = "0x23ecf45a978D83Ed8697349d903b680FA31de9E8"

NODE_URL = os.environ.get("W3_NODE_URL")
NODE_WS_URL = os.environ.get("W3_NODE_WS_URL")
PRIVATE_KEY = os.environ.get("W3_PRIVATE_KEY")



class _Contract:
    WEB3 = Web3(Web3.HTTPProvider(NODE_URL))
    WEB3_WS = Web3(Web3.WebsocketProvider(NODE_WS_URL))
    SETUP_COMPLETED = False
    CONTRACT = None
    CONTRACT_WS = None
    CONTRACT_ADDRESS = None
    ABI_PATH = ""
    account = Account.from_key(PRIVATE_KEY)

    @classmethod
    def setUp(cls):
        if not cls.SETUP_COMPLETED:
            print("setting up")
            try:
                cls.WEB3.middleware_onion.add(construct_sign_and_send_raw_middleware(cls.account))
                cls.WEB3.middleware_onion.inject(geth_poa_middleware, layer=0)

                cls.WEB3_WS.middleware_onion.add(construct_sign_and_send_raw_middleware(cls.account))
                cls.WEB3_WS.middleware_onion.inject(geth_poa_middleware, layer=0)
                cls.SETUP_COMPLETED=True
            except:
                pass


    @classmethod
    def web3(cls):
        cls.setUp()
        return cls.WEB3

    @classmethod
    def web3ws(cls):
        cls.setUp()
        return cls.WEB3_WS

    @classmethod
    def get_ws(cls):
        if not cls.CONTRACT_WS:
            cls.setUp()
            with open(cls.ABI_PATH, 'r') as f:
                content = f.read()
                data = json.loads(content)
                abi = data['abi']
            cls.CONTRACT_WS = cls.WEB3_WS.eth.contract(address=cls.CONTRACT_ADDRESS, abi=abi)
        return cls.CONTRACT_WS

    @classmethod
    def get(cls):
        if not cls.CONTRACT:
            cls.setUp()
            with open(cls.ABI_PATH, 'r') as f:
                content = f.read()
                data = json.loads(content)
                abi = data['abi']
            cls.CONTRACT = cls.WEB3.eth.contract(address=cls.CONTRACT_ADDRESS, abi=abi)
        return cls.CONTRACT


class PriceFeedContract(_Contract):
    WEB3 = Web3(Web3.HTTPProvider(NODE_URL))
    WEB3_WS = Web3(Web3.WebsocketProvider(NODE_WS_URL))
    CONTRACT = None
    CONTRACT_WS = None
    account = Account.from_key(PRIVATE_KEY)

    CONTRACT_ADDRESS = PF_ADDRESS
    ABI_PATH = PF_ABI
    SETUP_COMPLETED = False

    @classmethod
    def is_symbol_active(cls, symbol):
        contract = cls.get()
        return contract.functions.checkSymbolActive(symbol).call()



class PredictContract(_Contract):
    WEB3 = Web3(Web3.HTTPProvider(NODE_URL))
    WEB3_WS = Web3(Web3.WebsocketProvider(NODE_WS_URL))
    CONTRACT = None
    CONTRACT_WS = None
    account = Account.from_key(PRIVATE_KEY)

    CONTRACT_ADDRESS = PM_ADDRESS
    ABI_PATH = PM_ABI
    SETUP_COMPLETED = False

    @classmethod
    def add_user(cls, address):
        contract = cls.get()
        return contract.functions.addUser(address).transact({'from': cls.account.address}).hex()

    @classmethod
    def is_user(cls, address):
        contract = cls.get()
        return contract.functions.isUser(address).call()

    @classmethod
    def create_prediction(cls, user, pred_time, symbol, direction, duration, ipfsCID):
        contract = cls.get()
        return contract.functions.createPrediction(
                user, pred_time, symbol, direction, duration, ipfsCID
            ).transact({'from': cls.account.address}).hex()



def run_example():
    add_user = "0x1139172fd1d654B3c77Ea40D3242a336F9495118"

    # read example 
    contract = PredictContract.get()
    print(contract.functions.isUser(add_user).call())

    # write example
    print(contract.functions.addUser(add_user).transact({'from': PredictContract.account.address}))
    print(contract.functions.isUser(add_user).call())

if __name__ == '__main__':
    run_example()
