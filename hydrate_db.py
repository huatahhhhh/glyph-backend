"""
cache db of block events
polling strategy of 5 minutes, configurable 
query events from block START to latest
update block number in db
"""
import json
import pprint
import time
import sqlite3
from contract import PriceFeedContract, PredictContract, _Contract

pp = pprint.PrettyPrinter(indent=4)

DB_NAME = "glyph_bot.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

def get_events(from_block, to_block, contract_class: _Contract, dump=False):
    contract = contract_class.get_ws()
    #web3 = contract_class.web3ws()
    filter_kwargs = {'fromBlock': from_block, 'toBlock': to_block}
    event_names = [event for event in dir(contract.events) if '_' not in event and event!='abi']

    all_logs = []
    for event_name in event_names:
        print(event_name)
        c_event = getattr(contract.events, event_name)
        filter_ = c_event.createFilter(**filter_kwargs)
        logs = filter_.get_all_entries()
        for log in logs:
           all_logs.append(dict(log))

    # sort
    def sort_key(log):
        return int(log['blockNumber']) * 1e8 + int(log['transactionIndex']) * 1e4 + int(log['logIndex'])

    all_logs = sorted(all_logs, key=sort_key)
    for log in all_logs:
        log['args'] = dict(log['args'])
        log['transactionHash'] = str(log['transactionHash'])
        log['blockHash'] = str(log['blockHash'])

    pp.pprint(all_logs)
    if dump:
        data = json.dumps(all_logs, indent=2)
        with open(f'{contract_class.__name__}.event_dump', 'w') as f:
            f.write(data)
    return all_logs

def handle_data(data):
    #print(data)
    # do necessary things in the db
    for event in data:
        pp.pprint(event)
        event_type= event['event']
        args = event['args']

        if event_type == 'SymbolActivatedEvent':
            activate_symbol(args)

        elif event_type == 'SymbolActivatedEvent':
            deactivate_symbol(args)

        # elif event_type == 'UserAdded':
            # add_user(args)

        # elif event_type == 'UserRemoved':
            # remove_user(args)

        elif event_type == 'PredictionCreated':
            create_prediction(args)

        elif event_type == 'PredictionCompleted':
            complete_prediction(args)

        # elif event_type == 'PredictionExpired':
            # expire_prediction(args)

        elif event_type == 'UseScoreUpdated':
            update_user_score(args)

def activate_symbol(args):
    # check if exists
    symbol = args['symbol']
    res = c.execute(f"SELECT * FROM Symbol WHERE symbol='{symbol}'");
    if len(res.fetchall())==0:
        c.execute(f"INSERT INTO Symbol VALUES ('{symbol}', 1)");
    else:
        c.execute(f"UPDATE Symbol SET active=1 WHERE symbol='{symbol}'");
    conn.commit()

def deactivate_symbol(args):
    symbol = args['symbol']
    res = c.execute(f"SELECT * FROM Symbol WHERE symbol='{symbol}'");
    if len(res.fetchall())==0:
        assert False
    else:
        c.execute(f"UPDATE Symbol SET active=0 WHERE symbol='{symbol}'");
    conn.commit()

# def add_user(args):
    # address = args['_address']
    # c.execute(f"INSERT INTO User VALUES (null, '{address}')");

# def remove_user(args):
    # address = args['_address']
    # c.execute(f"INSERT INTO User VALUES (null, '{address}')");

def create_prediction(args):
    c.execute(f"""
        INSERT INTO Prediction VALUES(
        '{args['user']}',
        {args['predTimestamp']},
        '{args['symbol']}',
        {args['predDirection']},
        {args['predDuration']},
        {args['initialPrice']},
        {args['initialPriceTimestamp']},
        null,
        null,
        'created'
        )
    """)
    conn.commit()
    

def complete_prediction(args):
    c.execute(f"""
    UPDATE Prediction SET
        final_price={args['finalPrice']},
        final_price_on={args['finalPriceTimestamp']},
        status='completed'
    WHERE 
    address='{args['user']}' AND
    predicted_on={args['predTimestamp']} AND
    symbol='{args['symbol']}'
    """)
    conn.commit()

def update_user_score(args):
    pass

def get_last_block_db():
    exists = c.execute("SELECT * FROM ChainUpdate").fetchall()
    if not exists:
        return None
    print(exists)
    return exists[0][0]

def set_last_block_db(block_id):
    # if block is earlier assert false
    exists = c.execute("SELECT * FROM ChainUpdate").fetchall()
    if not exists:
        c.execute(f"INSERT INTO ChainUpdate VALUES ({block_id})")
    else:
        c.execute(f"UPDATE ChainUpdate SET last_updated_block_id={block_id}")
    conn.commit()


if __name__ == "__main__":
    # TODO get latest block and dump
    START_BLOCK = 29201633
    BLOCK_INTERVAL = 9500
    last_block_check = get_last_block_db()
    if not last_block_check:
        last_block_check = START_BLOCK

    web3 = PriceFeedContract.web3ws()
    latest_block = web3.eth.get_block('latest')['number']

    while last_block_check < latest_block:
        from_block = last_block_check+1
        last_block_check += from_block + BLOCK_INTERVAL
        if last_block_check > latest_block:
            last_block_check = latest_block

        print("from block", from_block)
        print("to block", last_block_check)
        data1 = get_events(from_block, last_block_check, PriceFeedContract, dump=True)
        data2 = get_events(from_block, last_block_check, PredictContract, dump=True)
        data = data1 + data2
        handle_data(data)
        set_last_block_db(last_block_check)

    # with open("./PredictContract.event_dump2", 'r') as f:
        # data = json.loads(f.read())
    # handle_data(data)
