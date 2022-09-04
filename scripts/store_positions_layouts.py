from web3 import Web3
from scripts.helpful_scripts import get_account
from brownie import PlayerRate
import json


def store_positions(contract_address, account=None):
    account = account if account else get_account()
    player_rate = PlayerRate.at(contract_address)
    positions_file = open("./constants/positions.json")
    positions_data = json.load(positions_file)

    print("Storing 100+ positions...")

    for i in range(100):
        store_position_tx = player_rate.storePosition(
            i, positions_data[str(i)], {"from": account}
        )
        store_position_tx.wait(1)

    store_position_tx = player_rate.storePosition(
        "110", positions_data["110"], {"from": account}
    )
    store_position_tx.wait(1)

    print("Positions stored")


def store_layouts(contract_address, account=None):
    account = account if account else get_account()
    player_rate = PlayerRate.at(contract_address)
    layouts_file = open("./constants/layouts.json")
    layouts_data = json.load(layouts_file)

    print("Storing layouts...")

    for i in range(len(layouts_data["layouts"])):
        store_layout_tx = player_rate.storeLayout(
            i, layouts_data["layouts"][i]["positions"], {"from": account}
        )
        store_layout_tx.wait(1)

    print("Layouts stored")
