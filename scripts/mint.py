from web3 import Web3
import time
from scripts.helpful_scripts import get_account, POLYGON_TESTNET
from brownie import VerifiableRandomFootballer, network


def mint():
    if network.show_active() in POLYGON_TESTNET:
        verifiable_random_footballer = VerifiableRandomFootballer.at(
            "0xD7A8585B195b595A973090Abb8406E3029D9cFe3"
        )
        owner = get_account()
        request_tx = verifiable_random_footballer.requestPlayer(
            {"from": owner, "value": Web3.toWei(0.1, "ether")}
        )
        request_tx.wait(1)
        token_id = request_tx.events["requestedPlayer"]["tokenId"]
        time.sleep(60)
        generate_tx = verifiable_random_footballer.generatePlayer(
            token_id, {"from": owner, "gasLimit": 5700000}
        )
        generate_tx.wait(1)
        print(f"Token URI : {verifiable_random_footballer.tokenURI(token_id)}")


def main():
    mint()
