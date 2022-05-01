from web3 import Web3
from scripts.helpful_scripts import get_account, get_contract, fund_with_link
from brownie import (
    VerifiableRandomFootballer,
    Base64,
    SvgLib,
    MetadataLib,
    KickToken,
    PlayerTransfer,
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
    print("Contracts deployed")

    # mint_nft(verifiable_random_footballer)
    return (verifiable_random_footballer, kick_token, player_transfer)


def mint_nft(verifiable_random_footballer):
    owner = get_account()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 5646849848180055
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    generate_tx = verifiable_random_footballer.generatePlayer(token_id, {"from": owner})
    generate_tx.wait(1)
    print(f"Token URI : {verifiable_random_footballer.tokenURI(token_id)}")


def main():
    deploy()
