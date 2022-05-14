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
    player_loan = PlayerLoan.at("0x129a1Df192AE111b1D884609f32e76b8f103ECBD")
    PlayerLoan.publish_source(player_loan)
    player_transfer = PlayerTransfer.at("0x26342b83257DE4F2464c9324b69908372E272854")
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
    league_team = LeagueTeam.at("0xf4322b3A8b07C8200b229a85E81885adC2401E54")
    LeagueTeam.publish_source(league_team)
    league_game = LeagueGame.at("0x83021C72E3de6F7720b18290Faf407EFa0B40e70")
    LeagueGame.publish_source(league_game)
    player_rate = PlayerRate.at("0x3b1b94C16E10800307596cBC483412fec8B6C969")
    PlayerRate.publish_source(player_rate)
    game_result = GameResult.at("0x308ED2068D0FbA5D7d7c9836A83edDDB50692E6e")
    GameResult.publish_source(game_result)
    claim_kick_token = ClaimKickToken.at("0x996198DF82B0773123a6405Bf978cA1426Cae6F6")
    ClaimKickToken.publish_source(claim_kick_token)


def main():
    verify()
