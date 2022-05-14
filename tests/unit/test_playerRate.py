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
from brownie.network.state import Chain


def test_can_sign_up_player():
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
    # Change the delays in which the game will be set to make it shorter to test
    set_tx = league_game.setGameDelay([0, 5], {"from": owner})
    set_tx.wait(1)
    request_tx = league_game.requestGame(first_team_id, second_team_id, {"from": owner})
    request_tx.wait(1)
    request_id = request_tx.events["gameRequested"]["requestId"]
    random_number = 5460505
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, league_game.address
    )
    # Change the preregistration to avoid setting it before the first block of the local chain
    set_tx = player_rate.setPreRegistration(3, {"from": owner})
    set_tx.wait(1)

    chain = Chain()
    game_id = league_game.teamGame(second_team_id, 1)
    home_team = league_game.games(game_id, 1)
    if home_team == second_team_id:
        position_id = 5
    else:
        position_id = 20

    # Signing up a player with an account not owner should fail:
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.signUpPlayer(
            captain_id, second_team_id, game_id, position_id, {"from": owner}
        )

    if home_team == first_team_id:
        position_id = 5
    else:
        position_id = 20

    # Signing up a player in the other team should fail:
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.signUpPlayer(
            captain_id, first_team_id, game_id, position_id, {"from": not_owner}
        )

    # Signing up a player on a position of the other team should fail:
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.signUpPlayer(
            captain_id, second_team_id, game_id, position_id, {"from": not_owner}
        )

    if home_team == second_team_id:
        position_id = 5
    else:
        position_id = 20

    sign_up_tx = player_rate.signUpPlayer(
        captain_id, second_team_id, game_id, position_id, {"from": not_owner}
    )
    sign_up_tx.wait(1)
    blockSigned = len(chain) - 1

    assert player_rate.gamePlayers(game_id, position_id) == (
        captain_id,
        blockSigned,
        0,
        0,
    )
    assert player_rate.isPlayerSignedUp(captain_id) == True
    assert sign_up_tx.events["playerSignedUp"]["gameId"] == game_id
    assert sign_up_tx.events["playerSignedUp"]["playerId"] == captain_id
    assert sign_up_tx.events["playerSignedUp"]["position"] == position_id

    # Signing up a player already signed should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.signUpPlayer(
            captain_id, second_team_id, game_id, position_id + 1, {"from": not_owner}
        )

    # Mint another player and apply him to second team
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    player_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 876
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(player_id, second_team_id, {"from": owner})
    apply_tx.wait(1)
    validate_tx = league_team.validateApplication(
        player_id, second_team_id, {"from": not_owner}
    )
    validate_tx.wait(1)

    # Signing up a player for a position already occupied should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.signUpPlayer(
            player_id, second_team_id, game_id, position_id, {"from": owner}
        )


def test_can_calculate_players_rates():
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
    set_tx = league_game.setGameDelay([0, 5], {"from": owner})
    set_tx.wait(1)
    request_tx = league_game.requestGame(first_team_id, second_team_id, {"from": owner})
    request_tx.wait(1)
    request_id = request_tx.events["gameRequested"]["requestId"]
    random_number = 5460505
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, league_game.address
    )
    set_tx = player_rate.setPreRegistration(3, {"from": owner})
    set_tx.wait(1)
    game_id = league_game.teamGame(second_team_id, 1)
    home_team = league_game.games(game_id, 1)
    if home_team == second_team_id:
        position_id = 6
    else:
        position_id = 22

    chain = Chain()
    blockSigned = len(chain)
    sign_up_tx = player_rate.signUpPlayer(
        captain_id, second_team_id, game_id, position_id, {"from": not_owner}
    )
    sign_up_tx.wait(1)

    # Calculate the rates before the end of the game should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.setPlayerRates(game_id, {"from": owner})

    # Change the duration of the game to make it shorter to test
    set_tx = player_rate.setGameDuration(3, {"from": owner})
    set_tx.wait(1)

    calculate_tx = player_rate.setPlayerRates(game_id, {"from": owner})
    calculate_tx.wait(1)

    assert player_rate.playerLastGame(captain_id) == game_id
    assert player_rate.isPlayerSignedUp(captain_id) == False
    assert player_rate.gamePlayers(game_id, position_id) == (
        captain_id,
        blockSigned,
        5,
        11,
    )


def test_can_set_game_duration():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        _,
        _,
        _,
        _,
        _,
        _,
        player_rate,
        _,
        _,
    ) = deploy()

    # Change the prices from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.setGameDuration(3000, {"from": not_owner})

    set_tx = player_rate.setGameDuration(3000, {"from": owner})
    set_tx.wait(1)

    assert player_rate.gameDuration() == 3000
    assert set_tx.events["updateGameDuration"]["duration"] == 3000


def test_can_set_duration_between_games():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        _,
        _,
        _,
        _,
        _,
        _,
        player_rate,
        _,
        _,
    ) = deploy()

    # Change the prices from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.setDurationBetweenGames(300000, {"from": not_owner})

    set_tx = player_rate.setDurationBetweenGames(300000, {"from": owner})
    set_tx.wait(1)

    assert player_rate.durationBetweenGames() == 300000
    assert set_tx.events["updateDurationBetweenGames"]["duration"] == 300000


def test_can_set_preregistration():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        _,
        _,
        _,
        _,
        _,
        _,
        player_rate,
        _,
        _,
    ) = deploy()

    # Change the prices from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_rate.setPreRegistration(300000, {"from": not_owner})

    set_tx = player_rate.setPreRegistration(300000, {"from": owner})
    set_tx.wait(1)

    assert player_rate.preRegistration() == 300000
    assert set_tx.events["updatePreRegistration"]["duration"] == 300000
