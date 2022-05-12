from web3 import Web3
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
    fund_with_link,
)
from scripts.deploy import deploy
from brownie import network, exceptions


def test_can_set_game_result_contract():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    (
        verifiable_random_footballer,
        _,
        _,
        _,
        _,
        league_game,
        _,
        _,
    ) = deploy()

    # Set the address if already set should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.setGameResultContract(
            verifiable_random_footballer.address, {"from": owner}
        )


def test_can_finish_game():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        _,
        _,
        league_team,
        league_game,
        player_rate,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    fund_with_link(league_game.address, owner, None, Web3.toWei(100, "ether"))
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    captain_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(captain_id, {"from": owner})
    create_tx.wait(1)
    first_team_id = create_tx.events["teamCreation"]["teamId"]
    approve_tx = kick_token.approve(
        league_game.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    sign_up_team_tx = league_game.signUpTeam(
        first_team_id, 8, Web3.toWei(4, "ether"), {"from": owner}
    )
    sign_up_team_tx.wait(1)
    send_tx = kick_token.transfer(
        not_owner, kick_token.balanceOf(owner), {"from": owner}
    )
    send_tx.wait(1)
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    captain_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 5665498700435978654
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    generate_tx = verifiable_random_footballer.generatePlayer(
        captain_id, {"from": not_owner}
    )
    generate_tx.wait(1)
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(captain_id, {"from": not_owner})
    create_tx.wait(1)
    second_team_id = create_tx.events["teamCreation"]["teamId"]
    approve_tx = kick_token.approve(
        league_game.address, Web3.toWei(1000, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    sign_up_team_tx = league_game.signUpTeam(
        second_team_id, 8, Web3.toWei(5, "ether"), {"from": not_owner}
    )
    sign_up_team_tx.wait(1)
    set_tx = league_game.setChallengeTime(0, {"from": owner})
    set_tx.wait(1)
    challenge_tx = league_game.challengeTeam(
        first_team_id, second_team_id, {"from": owner}
    )
    challenge_tx.wait(1)
    set_tx = league_game.setGameDelay([0, 1], {"from": owner})
    set_tx.wait(1)
    request_tx = league_game.requestGame(first_team_id, second_team_id, {"from": owner})
    request_tx.wait(1)
    request_id = request_tx.events["gameRequested"]["requestId"]
    random_number = 5460505
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, league_game.address
    )
    set_tx = player_rate.setPreRegistration(0, {"from": owner})
    set_tx.wait(1)
    game_id = league_game.teamGame(second_team_id, 1)
    home_team = league_game.games(game_id, 1)
    if home_team == second_team_id:
        position_id = 6
    else:
        position_id = 22
    sign_up_tx = player_rate.signUpPlayer(
        captain_id, second_team_id, game_id, position_id, {"from": not_owner}
    )
    sign_up_tx.wait(1)

    # Shorten game duration in order to be able to finish the game
    set_tx = player_rate.setGameDuration(2, {"from": owner})
    set_tx.wait(1)

    # Finishing the game when the contract is not funded should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.finishGame(game_id, {"from": owner})

    # Fund the contract
    send_tx = kick_token.transfer(
        league_game.address, Web3.toWei(100, "ether"), {"from": not_owner}
    )
    send_tx.wait(1)
    old_loser_balance = kick_token.balanceOf(owner)
    old_winner_balance = kick_token.balanceOf(not_owner)
    finish_tx = league_game.finishGame(game_id, {"from": owner})
    finish_tx.wait(1)

    assert league_game.teamGame(first_team_id, 0) == 0
    assert league_game.teamGame(first_team_id, 1) == 0
    assert league_game.teamGame(first_team_id, 2) == 0
    assert league_game.teamGame(first_team_id, 3) == 0
    assert league_game.teamGame(second_team_id, 0) == 0
    assert league_game.teamGame(second_team_id, 1) == 0
    assert league_game.teamGame(second_team_id, 2) == 0
    assert league_game.teamGame(second_team_id, 3) == 0
    assert kick_token.balanceOf(owner) == old_loser_balance
    assert kick_token.balanceOf(not_owner) == old_winner_balance + Web3.toWei(
        4 + 5 + 2, "ether"
    )
    assert finish_tx.events["gameFinished"]["gameId"] == game_id
    assert finish_tx.events["gameFinished"]["result"] == 2

    # Fund the contract
    send_tx = kick_token.transfer(
        league_game.address, Web3.toWei(100, "ether"), {"from": not_owner}
    )
    send_tx.wait(1)

    # Finishing the game twice should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.finishGame(game_id, {"from": owner})
