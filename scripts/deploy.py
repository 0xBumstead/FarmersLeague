from web3 import Web3
from scripts.helpful_scripts import get_account, get_contract, fund_with_link
from brownie import (
    VerifiableRandomFootballer,
    Base64,
    SvgLib,
    MetadataLib,
    KickToken,
    PlayerTransfer,
    PlayerLoan,
    config,
    network,
)


def deploy():
    print("Deploying contracts...")
    account = get_account()
    Base64.deploy({"from": account})
    SvgLib.deploy({"from": account})
    MetadataLib.deploy({"from": account})
    verifiable_random_footballer = VerifiableRandomFootballer.deploy(
        get_contract("vrf_coordinator"),
        get_contract("link_token"),
        config["networks"][network.show_active()]["keyhash"],
        config["networks"][network.show_active()]["fee"],
        Web3.toWei(0.1, "ether"),
        {"from": account},
    )
    kick_token = KickToken.deploy({"from": account})
    player_transfer = PlayerTransfer.deploy(
        kick_token.address, verifiable_random_footballer.address, {"from": account}
    )
    player_loan = PlayerLoan.deploy(
        kick_token.address, verifiable_random_footballer.address, {"from": account}
    )
    print("Contracts deployed")

    return (verifiable_random_footballer, kick_token, player_transfer, player_loan)


def main():
    deploy()
