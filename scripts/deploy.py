from web3 import Web3
from scripts.helpful_scripts import get_account, get_contract
from brownie import (
    VerifiableRandomFootballer,
    Base64,
    SvgLib,
    MetadataLib,
    KickToken,
    PlayerLoan,
    PlayerTransfer,
    LeagueTeam,
    LeagueGame,
    PlayerRate,
    GameResult,
    ClaimKickToken,
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
    player_loan = PlayerLoan.deploy(
        kick_token.address, verifiable_random_footballer.address, {"from": account}
    )
    player_transfer = PlayerTransfer.deploy(
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
    league_game = LeagueGame.deploy(
        kick_token.address,
        league_team.address,
        verifiable_random_footballer.address,
        player_loan.address,
        get_contract("vrf_coordinator"),
        get_contract("link_token"),
        config["networks"][network.show_active()]["keyhash"],
        config["networks"][network.show_active()]["fee"],
        {"from": account},
    )
    player_rate = PlayerRate.deploy(
        league_game.address,
        league_team.address,
        verifiable_random_footballer.address,
        player_loan.address,
        {"from": account},
    )
    game_result = GameResult.deploy(
        player_rate.address, league_game.address, {"from": account}
    )
    set_contract_address_tx = league_game.setGameResultContract(
        game_result.address, {"from": account}
    )
    set_contract_address_tx.wait(1)
    claim_kick_token = ClaimKickToken.deploy(
        kick_token.address, verifiable_random_footballer.address, {"from": account}
    )
    transfer_kick = kick_token.transfer(
        claim_kick_token, Web3.toWei(10000 * 100, "ether"), {"from": account}
    )
    transfer_kick.wait(1)
    print("Contracts deployed")

    return (
        verifiable_random_footballer,
        kick_token,
        player_transfer,
        player_loan,
        league_team,
        league_game,
        player_rate,
        game_result,
        claim_kick_token,
    )


def main():
    deploy()
