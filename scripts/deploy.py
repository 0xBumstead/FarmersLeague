from web3 import Web3
from scripts.helpful_scripts import get_account, get_contract
from brownie import (
    VerifiableRandomFootballer,
    Base64,
    SvgLib,
    MetadataLib,
    KickToken,
    PlayerTransfer,
    PlayerLoan,
    LeagueTeam,
    config,
    network,
)


def deploy():
    print("Deploying contracts...")
    account = get_account()
    """
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
    league_team = LeagueTeam.deploy(
        kick_token.address,
        verifiable_random_footballer.address,
        player_loan.address,
        Web3.toWei(10, "ether"),
        Web3.toWei(5, "ether"),
        {"from": account},
    )
    """
    league_team = LeagueTeam.deploy(
        "0xCBb1a5BeC29b33225878042F4294832fb5D6768b",
        "0xD7A8585B195b595A973090Abb8406E3029D9cFe3",
        "0x129a1Df192AE111b1D884609f32e76b8f103ECBD",
        Web3.toWei(10, "ether"),
        Web3.toWei(5, "ether"),
        {"from": account},
    )
    print("Contracts deployed")

    return (
        # verifiable_random_footballer,
        # kick_token,
        # player_transfer,
        # player_loan,
        league_team,
    )


def main():
    deploy()
