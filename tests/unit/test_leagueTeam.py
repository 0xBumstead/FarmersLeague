from web3 import Web3
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
    fund_with_link,
)
from scripts.deploy import deploy
from brownie import network, exceptions
import pytest


def test_can_create_team():
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
        player_loan,
        league_team,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    # Mint a player (no need to generate metadata here)
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Approve the transfer of KICK token from the leagueTeam contract
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)

    # Transfer all the Kick tokens from owner to not_owner
    send_tx = kick_token.transfer(
        not_owner, kick_token.balanceOf(owner), {"from": owner}
    )
    send_tx.wait(1)

    # Create a team from an account not owner of the player should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.createTeam(token_id, {"from": not_owner})

    # Create a team from an account without KICK should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.createTeam(token_id, {"from": owner})

    # Transfer all the Kick tokens from not_owner to owner
    send_tx = kick_token.transfer(
        owner, kick_token.balanceOf(not_owner), {"from": not_owner}
    )
    send_tx.wait(1)

    # Create a team
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)

    # Create a team with a player already member of a team should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.createTeam(token_id, {"from": owner})

    assert kick_token.balanceOf(league_team) == Web3.toWei(10, "ether")
    assert league_team.teamMembers(1, 0) == 1
    assert league_team.teamMembers(1, 1) == token_id
    assert league_team.playersTeam(token_id) == 1
    assert create_tx.events["teamCreation"]["teamId"] == 1
    assert create_tx.events["teamCreation"]["captainId"] == token_id
    assert league_team.nbOfTeams() == 1

    # Mint a second player (no need to generate metadata here)
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    # List for loan the player
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)
    # Send KICK token to not owner to pay for the loan
    send_tx = kick_token.transfer(not_owner, Web3.toWei(2, "ether"), {"from": owner})
    send_tx.wait(1)
    approve_tx = kick_token.approve(
        player_loan, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    # Send the player on loan
    loan_tx = player_loan.loan(token_id, {"from": not_owner})
    loan_tx.wait(1)

    # Create a team with a player on loan should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.createTeam(token_id, {"from": owner})


def test_can_remove_team():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        _,
        player_loan,
        league_team,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)

    # Remove a team from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.removeTeam(token_id, {"from": not_owner})

    # Remove a team
    remove_tx = league_team.removeTeam(token_id, {"from": owner})
    remove_tx.wait(1)

    assert league_team.playersTeam(token_id) == 0
    assert league_team.teamMembers(1, 0) == 0
    assert remove_tx.events["teamRemoval"]["teamId"] == 1

    # Remove a non existent team should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.removeTeam(token_id, {"from": owner})

    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)
    send_tx = kick_token.transfer(not_owner, Web3.toWei(2, "ether"), {"from": owner})
    send_tx.wait(1)
    approve_tx = kick_token.approve(
        player_loan, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    loan_tx = player_loan.loan(token_id, {"from": not_owner})
    loan_tx.wait(1)

    # Create a team with a player on loan should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.removeTeam(token_id, {"from": owner})


def test_can_apply_for_team():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        _,
        player_loan,
        league_team,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)
    team_id = create_tx.events["teamCreation"]["teamId"]
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Apply with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.applyForTeam(token_id, team_id, {"from": not_owner})

    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": owner})
    apply_tx.wait(1)

    assert league_team.teamApplications(team_id, 0) == 1
    assert league_team.teamApplications(team_id, 1) == token_id
    assert league_team.playersApplication(token_id) == team_id
    assert apply_tx.events["playerApplication"]["teamId"] == team_id
    assert apply_tx.events["playerApplication"]["playerId"] == token_id

    # Apply from a player already having an application should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.applyForTeam(token_id, team_id, {"from": owner})

    # Validate the player application
    validate_tx = league_team.validateApplication(token_id, team_id, {"from": owner})
    validate_tx.wait(1)

    # Apply from a player already having a team should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.applyForTeam(token_id, team_id, {"from": owner})

    # Mint another player and send it on loan
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 12345
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)
    send_tx = kick_token.transfer(not_owner, Web3.toWei(2, "ether"), {"from": owner})
    send_tx.wait(1)
    approve_tx = kick_token.approve(
        player_loan, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    loan_tx = player_loan.loan(token_id, {"from": not_owner})
    loan_tx.wait(1)

    # Apply a player whose owner sent on loan should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.applyForTeam(token_id, team_id, {"from": owner})

    # Apply a player from its current owner (through the loan)
    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": not_owner})
    apply_tx.wait(1)

    # Fullfill the team with 21 more players
    for i in range(3, 24):
        request_tx = verifiable_random_footballer.requestPlayer(
            {"from": owner, "value": Web3.toWei(0.1, "ether")}
        )
        request_tx.wait(1)
        request_id = request_tx.events["requestedPlayer"]["requestId"]
        token_id = request_tx.events["requestedPlayer"]["tokenId"]
        random_number = 876 * i
        get_contract("vrf_coordinator").callBackWithRandomness(
            request_id, random_number, verifiable_random_footballer.address
        )
        apply_tx = league_team.applyForTeam(token_id, team_id, {"from": owner})
        apply_tx.wait(1)
        validate_tx = league_team.validateApplication(
            token_id, team_id, {"from": owner}
        )
        validate_tx.wait(1)

    # Mint one more player now that the team is full
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 876 * i
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Apply for a full team should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.applyForTeam(token_id, team_id, {"from": owner})


def test_can_cancel_application():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        _,
        player_loan,
        league_team,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)
    team_id = create_tx.events["teamCreation"]["teamId"]
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": not_owner})
    apply_tx.wait(1)

    # Cancel an application with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.cancelApplication(token_id, team_id, {"from": owner})

    cancel_tx = league_team.cancelApplication(token_id, team_id, {"from": not_owner})
    cancel_tx.wait(1)
    applications_number = league_team.teamApplications(team_id, 0)

    for i in range(1, applications_number):
        assert league_team.teamApplications(team_id, i) != token_id
    assert league_team.playersApplication(token_id) == 0
    assert cancel_tx.events["applicationCanceled"]["playerId"] == token_id
    assert cancel_tx.events["applicationCanceled"]["teamId"] == team_id

    # Mint another player and send it on loan
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 12345
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)
    send_tx = kick_token.transfer(not_owner, Web3.toWei(2, "ether"), {"from": owner})
    send_tx.wait(1)
    approve_tx = kick_token.approve(
        player_loan, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    loan_tx = player_loan.loan(token_id, {"from": not_owner})
    loan_tx.wait(1)
    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": not_owner})
    apply_tx.wait(1)

    # Cancel an application of a player whose owner sent on loan should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.cancelApplication(token_id, team_id, {"from": owner})

    # Cancel an application of a player from its current owner (through the loan)
    cancel_tx = league_team.cancelApplication(token_id, team_id, {"from": not_owner})
    cancel_tx.wait(1)


def test_can_validate_application():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        _,
        player_loan,
        league_team,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)
    team_id = create_tx.events["teamCreation"]["teamId"]
    captain_id = create_tx.events["teamCreation"]["captainId"]
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": not_owner})
    apply_tx.wait(1)

    # Validate an application from an account not owner of the team captain should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.validateApplication(token_id, team_id, {"from": not_owner})

    # Validate the player application
    players_number = league_team.teamMembers(team_id, 0)
    validate_tx = league_team.validateApplication(token_id, team_id, {"from": owner})
    validate_tx.wait(1)
    applications_number = league_team.teamApplications(team_id, 0)
    position = validate_tx.events["applicationValidated"]["position"]

    for i in range(1, applications_number):
        assert league_team.teamApplications(team_id, i) != token_id
    assert league_team.playersApplication(token_id) == 0
    assert validate_tx.events["applicationValidated"]["playerId"] == token_id
    assert validate_tx.events["applicationValidated"]["teamId"] == team_id
    assert league_team.teamMembers(team_id, 0) == players_number + 1
    assert league_team.playersTeam(token_id) == team_id
    for i in range(2, 24):
        if i == position:
            assert league_team.teamMembers(team_id, i) == token_id
        else:
            assert league_team.teamMembers(team_id, i) != token_id

    # Mint another player and make it apply
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 12345
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": owner})
    apply_tx.wait(1)
    # Send the captain on loan
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), captain_id, {"from": owner}
    )
    list_tx.wait(1)
    send_tx = kick_token.transfer(not_owner, Web3.toWei(2, "ether"), {"from": owner})
    send_tx.wait(1)
    approve_tx = kick_token.approve(
        player_loan, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    loan_tx = player_loan.loan(captain_id, {"from": not_owner})
    loan_tx.wait(1)

    # Validate an application while the captain is on loan, by using owner account should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.validateApplication(token_id, team_id, {"from": owner})

    # Fullfill the team with 20 more players (plus the captain and the first validated player, leaving one position open)
    for i in range(3, 23):
        request_tx = verifiable_random_footballer.requestPlayer(
            {"from": owner, "value": Web3.toWei(0.1, "ether")}
        )
        request_tx.wait(1)
        request_id = request_tx.events["requestedPlayer"]["requestId"]
        token_id = request_tx.events["requestedPlayer"]["tokenId"]
        random_number = 876 * i
        get_contract("vrf_coordinator").callBackWithRandomness(
            request_id, random_number, verifiable_random_footballer.address
        )
        apply_tx = league_team.applyForTeam(token_id, team_id, {"from": owner})
        apply_tx.wait(1)
        # Because of the loan, validation is now made from not_owner
        validate_tx = league_team.validateApplication(
            token_id, team_id, {"from": not_owner}
        )
        validate_tx.wait(1)

    # Mint two more players, and apply them both, now that the team is almost full
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id_23 = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 654321
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id_23, team_id, {"from": owner})
    apply_tx.wait(1)
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id_24 = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 9876
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id_24, team_id, {"from": owner})
    apply_tx.wait(1)

    # Validate the first one to fullfill the team
    validate_tx = league_team.validateApplication(
        token_id_23, team_id, {"from": not_owner}
    )
    validate_tx.wait(1)

    # Validating an application to a full team should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.validateApplication(token_id_24, team_id, {"from": not_owner})


def test_can_clear_applications():
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
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)
    team_id = create_tx.events["teamCreation"]["teamId"]
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id_1 = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id_1, team_id, {"from": not_owner})
    apply_tx.wait(1)
    # Mint a second player, and apply it, in order to have two applications to clear
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id_2 = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 654
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id_2, team_id, {"from": not_owner})
    apply_tx.wait(1)

    # Clear applications with an account not owner of the captain should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.clearApplications(team_id, {"from": not_owner})

    # Clear the applications to the team
    clear_tx = league_team.clearApplications(team_id, {"from": owner})
    clear_tx.wait(1)

    assert league_team.teamApplications(team_id, 0) == 2
    assert league_team.teamApplications(team_id, 1) == 0
    assert league_team.teamApplications(team_id, 2) == 0
    assert league_team.playersApplication(token_id_1) == 0
    assert league_team.playersApplication(token_id_2) == 0
    assert clear_tx.events["applicationsCleared"]["teamId"] == team_id


def test_can_release_player():
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
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)
    team_id = create_tx.events["teamCreation"]["teamId"]
    captain_id = create_tx.events["teamCreation"]["captainId"]
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": not_owner})
    apply_tx.wait(1)
    validate_tx = league_team.validateApplication(token_id, team_id, {"from": owner})
    validate_tx.wait(1)

    # Release a player with an account not owner of the captain should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.releasePlayer(token_id, team_id, {"from": not_owner})

    # Release the captain should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.releasePlayer(captain_id, team_id, {"from": owner})

    # Release the player
    release_tx = league_team.releasePlayer(token_id, team_id, {"from": owner})
    release_tx.wait(1)

    # Release a player not in the team should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.releasePlayer(token_id, team_id, {"from": owner})

    assert league_team.teamMembers(team_id, 0) == 1
    assert league_team.teamMembers(team_id, 2) == 0
    assert league_team.playersTeam(token_id) == 0
    assert release_tx.events["playerReleased"]["playerId"] == token_id
    assert release_tx.events["playerReleased"]["teamId"] == team_id


def test_can_pay_release_clause():
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
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)
    team_id = create_tx.events["teamCreation"]["teamId"]
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": not_owner})
    apply_tx.wait(1)
    validate_tx = league_team.validateApplication(token_id, team_id, {"from": owner})
    validate_tx.wait(1)
    approve_tx = kick_token.approve(
        league_team, Web3.toWei(5, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)

    # Pay clause with an account not having enough kick tokens should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.payReleaseClause(token_id, {"from": not_owner})

    # Pay clause with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.payReleaseClause(token_id, {"from": owner})

    send_tx = kick_token.transfer(not_owner, Web3.toWei(5, "ether"), {"from": owner})
    send_tx.wait(1)
    owner_balance = kick_token.balanceOf(owner)
    contract_balance = kick_token.balanceOf(league_team)
    # Pay release clause
    pay_tx = league_team.payReleaseClause(token_id, {"from": not_owner})
    pay_tx.wait(1)

    assert league_team.teamMembers(team_id, 0) == 1
    assert league_team.teamMembers(team_id, 2) == 0
    assert league_team.playersTeam(token_id) == 0
    assert kick_token.balanceOf(not_owner) == 0
    assert kick_token.balanceOf(owner) == owner_balance + Web3.toWei(
        5 * 9750 / 10000, "ether"
    )
    assert kick_token.balanceOf(league_team) == contract_balance + Web3.toWei(
        5 * 250 / 10000, "ether"
    )


def test_can_withdraw():
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
        _,
        _,
        _,
        _,
    ) = deploy()
    transfer_tx = kick_token.transfer(
        not_owner, kick_token.balanceOf(owner), {"from": owner}
    )
    transfer_tx.wait(1)
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": not_owner})
    create_tx.wait(1)

    # Withdraw with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.withdraw({"from": not_owner})

    withdraw_tx = league_team.withdraw({"from": owner})
    withdraw_tx.wait(1)

    assert kick_token.balanceOf(league_team) == 0
    assert kick_token.balanceOf(owner) == Web3.toWei(10, "ether")


def test_can_set_creation_price():
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
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(10, "ether"), {"from": owner}
    )
    approve_tx.wait(1)

    setPrice_tx = league_team.setTeamCreationPrice(
        Web3.toWei(20, "ether"), {"from": owner}
    )
    setPrice_tx.wait(1)

    assert (
        league_team.teamCreationPrice()
        == setPrice_tx.events["updateTeamCreationPrice"]["price"]
    )

    # Set the price with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.setTeamCreationPrice(Web3.toWei(30, "ether"), {"from": not_owner})

    # Creating a team with an approval of an amount corresponding to the former price should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.createTeam(token_id, {"from": owner})


def test_can_set_release_price():
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
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = kick_token.approve(
        league_team.address, Web3.toWei(1000, "ether"), {"from": owner}
    )
    approve_tx.wait(1)
    create_tx = league_team.createTeam(token_id, {"from": owner})
    create_tx.wait(1)
    team_id = create_tx.events["teamCreation"]["teamId"]
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 3434
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    apply_tx = league_team.applyForTeam(token_id, team_id, {"from": not_owner})
    apply_tx.wait(1)
    validate_tx = league_team.validateApplication(token_id, team_id, {"from": owner})
    validate_tx.wait(1)
    approve_tx = kick_token.approve(
        league_team, Web3.toWei(5, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    send_tx = kick_token.transfer(not_owner, Web3.toWei(5, "ether"), {"from": owner})
    send_tx.wait(1)

    setPrice_tx = league_team.setReleasePrice(Web3.toWei(20, "ether"), {"from": owner})
    setPrice_tx.wait(1)

    assert (
        league_team.releasePrice() == setPrice_tx.events["updateReleasePrice"]["price"]
    )

    # Set the price with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.setReleasePrice(Web3.toWei(30, "ether"), {"from": not_owner})

    # Pay clause with an approval of an amount corresponding to the former price should fail
    with pytest.raises(exceptions.VirtualMachineError):
        league_team.payReleaseClause(token_id, {"from": not_owner})
