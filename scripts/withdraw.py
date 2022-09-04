from web3 import Web3
from scripts.helpful_scripts import get_account, POLYGON_TESTNET
from brownie import VerifiableRandomFootballer, network


def withdraw():
    if network.show_active() in POLYGON_TESTNET:
        verifiable_random_footballer = VerifiableRandomFootballer.at(
            "0xD7A8585B195b595A973090Abb8406E3029D9cFe3"
        )
        owner = get_account()

        withdraw_amount = Web3.fromWei(verifiable_random_footballer.balance(), "ether")
        withdraw_tx = verifiable_random_footballer.withdraw({"from": owner})
        withdraw_tx.wait(1)

        print(f"Amount withdrawn : {withdraw_amount}")


def main():
    withdraw()
