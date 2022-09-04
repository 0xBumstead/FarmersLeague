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


def test_can_sign_up_team():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    # Get two different accounts
    owner = get_account()
    not_owner = get_account(index=1)
    # Deploy the contracts and fund for ChainLink VRF usage
    (
        verifiable_random_footballer,
        kick_token,
        _,
        _,
        league_team,
        league_game,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    fund_with_link(league_game.address, owner, None, Web3.toWei(100, "ether"))
    # Mint a player (no need to generate metadata here)
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
    # Approve the transfer of KICK token from the leagueTeam contract
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    # Create a team
    create_tx = league_team.createTeam(captain_id, {"from": owner})
    create_tx.wait(1)
    team_id = create_tx.events["teamCreation"]["teamId"]
    # Approve league game contract to spend Kick Token for owner and not owner
    approve_tx = kick_token.approve(
        league_game.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    approve_tx = kick_token.approve(
        league_game.address, Web3.toWei(1000, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)

    # Sign up a team with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.signUpTeam(team_id, 8, Web3.toWei(4, "ether"), {"from": not_owner})

    # Transfer all the Kick Token to second account
    send_tx = kick_token.transfer(
        not_owner, kick_token.balanceOf(owner), {"from": owner}
    )
    send_tx.wait(1)

    # Sign up a team with not enough Kick Token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.signUpTeam(team_id, 8, Web3.toWei(4, "ether"), {"from": owner})

    # Send back Kick Token to the owner
    send_tx = kick_token.transfer(owner, Web3.toWei(10, "ether"), {"from": not_owner})
    send_tx.wait(1)

    # Sign up a team with an incorrect layout should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.signUpTeam(team_id, 14, Web3.toWei(4, "ether"), {"from": owner})

    # Sign up a team with an incorrect stake should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.signUpTeam(team_id, 14, Web3.toWei(2, "ether"), {"from": owner})

    sign_up_team_tx = league_game.signUpTeam(
        team_id, 8, Web3.toWei(4, "ether"), {"from": owner}
    )
    sign_up_team_tx.wait(1)

    assert kick_token.balanceOf(owner) == Web3.toWei(6, "ether")
    assert kick_token.balanceOf(league_game) == Web3.toWei(4, "ether")
    assert league_game.teamGame(team_id, 0) == 1
    assert league_game.teamGame(team_id, 2) == 8
    assert league_game.teamGame(team_id, 3) == Web3.toWei(4, "ether")
    assert sign_up_team_tx.events["teamSignedUp"]["teamId"] == team_id

    # Sign up a team already signed should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.signUpTeam(team_id, 8, Web3.toWei(4, "ether"), {"from": owner})


def test_cancel_sign_up():
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
        _,
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
    team_id = create_tx.events["teamCreation"]["teamId"]
    approve_tx = kick_token.approve(
        league_game.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    approve_tx = kick_token.approve(
        league_game.address, Web3.toWei(1000, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    # Sign up a team
    sign_up_team_tx = league_game.signUpTeam(
        team_id, 8, Web3.toWei(4, "ether"), {"from": owner}
    )
    sign_up_team_tx.wait(1)

    # Cancel with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.cancelSignUp(team_id, {"from": not_owner})

    # Withdraw the funds from the contract to test revert when contract balance is too low
    withdraw_tx = league_game.withdraw({"from": owner})
    withdraw_tx.wait(1)

    # Cancel without funds in the contract should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.cancelSignUp(team_id, {"from": owner})

    # Fund back the contract
    send_tx = kick_token.transfer(league_game, Web3.toWei(4, "ether"), {"from": owner})
    send_tx.wait(1)

    # Cancel the signed up team
    cancel_tx = league_game.cancelSignUp(team_id, {"from": owner})
    cancel_tx.wait(1)

    assert kick_token.balanceOf(owner) == Web3.toWei(100000000, "ether") - Web3.toWei(
        10, "ether"
    ) - Web3.toWei(10000 * 100, "ether")
    assert kick_token.balanceOf(league_game) == Web3.toWei(0, "ether")
    assert league_game.teamGame(team_id, 0) == 0
    assert league_game.teamGame(team_id, 1) == 0
    assert league_game.teamGame(team_id, 2) == 0
    assert league_game.teamGame(team_id, 3) == 0
    assert cancel_tx.events["signUpCanceled"]["teamId"] == team_id

    # Cancel a team not signed up should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.cancelSignUp(team_id, {"from": owner})


def test_can_challenge_team():
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
        _,
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
    # Transfer all the Kick Token to second account
    send_tx = kick_token.transfer(
        not_owner, kick_token.balanceOf(owner), {"from": owner}
    )
    send_tx.wait(1)
    # Create and sign up a second team
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    captain_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 789
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
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

    # Challenge a team not signed up should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.challengeTeam(first_team_id, second_team_id, {"from": owner})

    sign_up_team_tx = league_game.signUpTeam(
        second_team_id, 8, Web3.toWei(4, "ether"), {"from": not_owner}
    )
    sign_up_team_tx.wait(1)

    # Challenge a team with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.challengeTeam(first_team_id, second_team_id, {"from": not_owner})

    # First team challenges second team
    challenge_tx = league_game.challengeTeam(
        first_team_id, second_team_id, {"from": owner}
    )
    challenge_tx.wait(1)
    chain = Chain()

    assert league_game.teamGame(first_team_id, 0) == 2
    assert league_game.teamGame(second_team_id, 0) == 3
    assert (
        league_game.teamChallenge(second_team_id, first_team_id)
        == len(chain) + 86400 - 1
    )
    assert challenge_tx.events["teamChallenged"]["challengedTeamId"] == second_team_id
    assert challenge_tx.events["teamChallenged"]["challengingTeamId"] == first_team_id

    # Create and sign up a third team
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    captain_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 555
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(captain_id, {"from": not_owner})
    create_tx.wait(1)
    third_team_id = create_tx.events["teamCreation"]["teamId"]
    approve_tx = kick_token.approve(
        league_game.address, Web3.toWei(1000, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    sign_up_team_tx = league_game.signUpTeam(
        third_team_id, 8, Web3.toWei(4, "ether"), {"from": not_owner}
    )
    sign_up_team_tx.wait(1)

    # Challenge a team with an already challenging team should fail:
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.challengeTeam(first_team_id, third_team_id, {"from": owner})


def test_can_decline_challenge():
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
        _,
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
    random_number = 789
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
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
        second_team_id, 8, Web3.toWei(4, "ether"), {"from": not_owner}
    )
    sign_up_team_tx.wait(1)
    challenge_tx = league_game.challengeTeam(
        first_team_id, second_team_id, {"from": owner}
    )
    challenge_tx.wait(1)

    # Send all the Kick Tokens to first account
    send_tx = kick_token.transfer(
        owner, kick_token.balanceOf(not_owner), {"from": not_owner}
    )
    send_tx.wait(1)

    # Decline a challenge with an account not owner of the challenged team should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.declineChallenge(second_team_id, first_team_id, {"from": owner})

    # Decline a challenge with an account with not enough Kick Token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.declineChallenge(second_team_id, first_team_id, {"from": not_owner})

    send_tx = kick_token.transfer(not_owner, Web3.toWei(1, "ether"), {"from": owner})
    send_tx.wait(1)
    contract_balance = kick_token.balanceOf(league_game)

    # Second team declines challenge
    decline_tx = league_game.declineChallenge(
        second_team_id, first_team_id, {"from": not_owner}
    )
    decline_tx.wait(1)

    assert kick_token.balanceOf(not_owner) == 0
    assert kick_token.balanceOf(league_game) == contract_balance + Web3.toWei(
        1, "ether"
    )
    assert league_game.teamGame(first_team_id, 0) == 1
    assert league_game.teamGame(second_team_id, 0) == 1
    assert league_game.teamChallenge(second_team_id, first_team_id) == 0
    assert decline_tx.events["challengeDeclined"]["challengedTeamId"] == second_team_id
    assert decline_tx.events["challengeDeclined"]["challengingTeamId"] == first_team_id

    # Decline a challenge from a team not challenged should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.declineChallenge(second_team_id, first_team_id, {"from": not_owner})


def test_can_request_game():
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
        _,
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
    random_number = 789
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
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
        second_team_id, 8, Web3.toWei(4, "ether"), {"from": not_owner}
    )
    sign_up_team_tx.wait(1)
    # Change the challenge time so we get faster to the point where a game can be requested
    set_tx = league_game.setChallengeTime(3, {"from": owner})
    set_tx.wait(1)
    challenge_tx = league_game.challengeTeam(
        first_team_id, second_team_id, {"from": owner}
    )
    challenge_tx.wait(1)

    # Request a game before the challenge deadline should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.requestGame(first_team_id, second_team_id, {"from": owner})

    # Remove Link Token from the contract
    withdraw_tx = league_game.withdrawLink({"from": owner})
    withdraw_tx.wait(1)

    # Request a game with no Link Token in the contract should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.requestGame(first_team_id, second_team_id, {"from": owner})

    # Put back link token in the contract
    fund_with_link(league_game.address, owner, None, Web3.toWei(100, "ether"))

    request_tx = league_game.requestGame(first_team_id, second_team_id, {"from": owner})
    request_tx.wait(1)

    assert league_game.teamGame(first_team_id, 0) == 4
    assert league_game.teamGame(second_team_id, 0) == 4
    assert league_game.teamGame(first_team_id, 1) == 1
    assert league_game.teamGame(second_team_id, 1) == 1
    assert league_game.games(1, 1) == first_team_id
    assert league_game.games(1, 2) == second_team_id
    assert request_tx.events["gameRequested"]["firstTeam"] == first_team_id
    assert request_tx.events["gameRequested"]["secondTeam"] == second_team_id
    assert request_tx.events["gameRequested"]["gameId"] == 1

    # Request a game for teams already in a game should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.requestGame(first_team_id, second_team_id, {"from": owner})


def test_can_set_game():
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
        _,
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
    random_number = 789
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
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
        second_team_id, 8, Web3.toWei(4, "ether"), {"from": not_owner}
    )
    sign_up_team_tx.wait(1)
    set_tx = league_game.setChallengeTime(0, {"from": owner})
    set_tx.wait(1)
    challenge_tx = league_game.challengeTeam(
        first_team_id, second_team_id, {"from": owner}
    )
    challenge_tx.wait(1)
    request_tx = league_game.requestGame(first_team_id, second_team_id, {"from": owner})
    request_tx.wait(1)

    # Use VRFCoordinatorMock to call fulfillRandomness
    request_id = request_tx.events["gameRequested"]["requestId"]
    random_number = 646549879713
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, league_game.address
    )
    chain = Chain()

    assert league_game.games(1, 0) > len(chain) + 43200
    assert league_game.games(1, 0) < len(chain) + 604800 + 43200


def test_can_set_challenge_time():
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
        league_game,
        _,
        _,
        _,
    ) = deploy()

    # Change the time from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.setChallengeTime(10, {"from": not_owner})

    set_tx = league_game.setChallengeTime(10, {"from": owner})
    set_tx.wait(1)

    assert league_game.challengeTime() == 10
    assert set_tx.events["updateChallengeTime"]["time"] == 10


def test_can_set_prices():
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
        league_game,
        _,
        _,
        _,
    ) = deploy()

    # Change the prices from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.setPrices(
            [Web3.toWei(6, "ether"), Web3.toWei(2, "ether"), Web3.toWei(1, "ether")],
            {"from": not_owner},
        )

    set_tx = league_game.setPrices(
        [Web3.toWei(6, "ether"), Web3.toWei(2, "ether"), Web3.toWei(1, "ether")],
        {"from": owner},
    )
    set_tx.wait(1)

    assert league_game.prices(0) == Web3.toWei(6, "ether")
    assert league_game.prices(1) == Web3.toWei(2, "ether")
    assert set_tx.events["updatePrices"]["signedUpPrice"] == Web3.toWei(6, "ether")
    assert set_tx.events["updatePrices"]["declinePrice"] == Web3.toWei(2, "ether")


def test_can_set_game_delay():
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
        league_game,
        _,
        _,
        _,
    ) = deploy()

    # Change the prices from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.setGameDelay([500, 1000], {"from": not_owner})

    set_tx = league_game.setGameDelay([500, 1000], {"from": owner})
    set_tx.wait(1)

    assert league_game.gameDelay(0) == 500
    assert league_game.gameDelay(1) == 1000
    assert set_tx.events["updateGameDelay"]["minTime"] == 500
    assert set_tx.events["updateGameDelay"]["maxTime"] == 1000


def test_can_withdraw_link():
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
        league_game,
        _,
        _,
        _,
    ) = deploy()
    link_token = get_contract("link_token")
    fund_with_link(league_game.address, owner, None, Web3.toWei(100, "ether"))

    # Withdraw from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.withdrawLink({"from": not_owner})

    owner_balance = Web3.fromWei(link_token.balanceOf(owner), "ether")
    withdraw_tx = league_game.withdrawLink({"from": owner})
    withdraw_tx.wait(1)

    assert Web3.fromWei(link_token.balanceOf(owner), "ether") == owner_balance + 100 + 1
    assert link_token.balanceOf(league_game) == 0


def test_can_withdraw_kick():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        _,
        kick_token,
        _,
        _,
        _,
        league_game,
        _,
        _,
        _,
    ) = deploy()
    send_tx = kick_token.transfer(
        league_game, Web3.toWei(100, "ether"), {"from": owner}
    )
    send_tx.wait(1)

    # Withdraw from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_game.withdraw({"from": not_owner})

    owner_balance = kick_token.balanceOf(owner)
    withdraw_tx = league_game.withdraw({"from": owner})
    withdraw_tx.wait(1)

    assert kick_token.balanceOf(owner) == owner_balance + Web3.toWei(100, "ether")
    assert kick_token.balanceOf(league_game) == 0
