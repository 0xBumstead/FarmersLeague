from brownie import (
    VerifiableRandomFootballer,
    SvgLib,
    MetadataLib,
    KickToken,
    PlayerTransfer,
    PlayerLoan,
    LeagueTeam,
    LeagueGame,
    PlayerRate,
    GameResult,
    ClaimKickToken,
)


def verify():
    player_loan = PlayerLoan.at("0xf3E85e0b61071113f07F496A565ad3F7567424A0")
    PlayerLoan.publish_source(player_loan)
    player_transfer = PlayerTransfer.at("0xDB19F45D8bB71626896Cc6610028Ec8f6D3cdb63")
    PlayerTransfer.publish_source(player_transfer)
    kick_token = KickToken.at("0xCBb1a5BeC29b33225878042F4294832fb5D6768b")
    KickToken.publish_source(kick_token)
    svg_lib = SvgLib.at("0x32702337a85f0BE80A288DFe3231F1b21519135F")
    SvgLib.publish_source(svg_lib)
    metadata_lib = MetadataLib.at("0x8501919210E2abDad5Da04D4A719d8c177Da6b33")
    MetadataLib.publish_source(metadata_lib)
    verifiable_random_footballer = VerifiableRandomFootballer.at(
        "0xD7A8585B195b595A973090Abb8406E3029D9cFe3"
    )
    VerifiableRandomFootballer.publish_source(verifiable_random_footballer)
    league_team = LeagueTeam.at("0xBC8765fe84598C70D48Ca3b3D63b9afe5Ff805B9")
    LeagueTeam.publish_source(league_team)
    league_game = LeagueGame.at("0x83CE4F977139EeB94d156429ED13F3A9089A0664")
    LeagueGame.publish_source(league_game)
    player_rate = PlayerRate.at("0xBA462de910068f4B3675c9C1A92F725E81CE4524")
    PlayerRate.publish_source(player_rate)
    game_result = GameResult.at("0xfB38A5E7B056dDa86CA5A2E494fC0c3ed5247076")
    GameResult.publish_source(game_result)
    claim_kick_token = ClaimKickToken.at("0x996198DF82B0773123a6405Bf978cA1426Cae6F6")
    ClaimKickToken.publish_source(claim_kick_token)


def main():
    verify()
