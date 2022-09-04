from web3 import Web3
from scripts.helpful_scripts import get_account, POLYGON_TESTNET
from brownie import LeagueGame, network


def set_params():
    if network.show_active() in POLYGON_TESTNET:
        league_game = LeagueGame.at("0x83CE4F977139EeB94d156429ED13F3A9089A0664")
        owner = get_account()

        set_game_delay_tx = league_game.setGameDelay([10000, 100000], {"from": owner})
        set_game_delay_tx.wait(1)
        set_challenge_time_tx = league_game.setChallengeTime(20000, {"from": owner})
        set_challenge_time_tx.wait(1)

        print("Game delays and challenge times reset")


def main():
    set_params()
