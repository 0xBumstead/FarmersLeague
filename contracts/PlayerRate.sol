// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./PlayerOwnership.sol";
import "../interfaces/ILeagueTeam.sol";
import "../interfaces/ILeagueGame.sol";
import "./PlayerOwnership.sol";

error TooEarly(uint256 time, uint256 requested);
error NotInTeam();
error AlreadySigned();
error IncorrectGameTeamPosition();
error NoCurrentGame();
error PositionNotAvailable();

contract PlayerRate is Ownable, PlayerOwnership {
    ILeagueTeam internal leagueTeam;
    ILeagueGame internal leagueGame;

    uint256 public gameDuration; // Number of blocks that lasts a game
    uint256 public durationBetweenGames; // Number of blocks that a team should wait between two games
    uint256 public preRegistration; // Number of blocks before game start where player registration is open
    struct playerSignUp {
        uint16 playerId;
        uint256 blockSigned;
        uint8 defenseRate;
        uint8 attackRate;
    }
    mapping(uint256 => playerSignUp[32]) public gamePlayers; // gameId => playerIds, blocks and rates signed up sorted by position
    mapping(uint16 => uint256) public playerLastGame; // playerId => most recent game player was part of
    mapping(uint16 => bool) public isPlayerSignedUp;
    // 16 first positions are for home team, 16 last positions are for away team
    mapping(uint8 => uint8) public positionIds; // matching the two different codes of positionId
    mapping(uint256 => mapping(uint8 => uint8)) public layoutPositions; // matching the positionsId with the positions list in each different layout

    event updateGameDuration(uint256 duration);
    event updateDurationBetweenGames(uint256 duration);
    event updatePreRegistration(uint256 duration);
    event playerSignedUp(uint256 gameId, uint16 playerId, uint8 position);

    constructor(
        address _LeagueGame,
        address _LeagueTeam,
        address _VerifiableRandomFootballer,
        address _PlayerLoan
    ) PlayerOwnership(_PlayerLoan, _VerifiableRandomFootballer) {
        leagueTeam = ILeagueTeam(_LeagueTeam);
        leagueGame = ILeagueGame(_LeagueGame);
        gameDuration = 2700; // 90 minutes
        preRegistration = 18000; // 10 hours
        durationBetweenGames = 302400; // a week

        // Corresponding id code for the position Ids between preferred and compatible position (in the players Metadata)
        positionIds[0] = 0; // DC
        positionIds[1] = 0; // DC
        positionIds[2] = 0; // DC
        positionIds[3] = 0; // DC
        positionIds[4] = 0; // DC
        positionIds[5] = 1; // DR
        positionIds[6] = 1; // DR
        positionIds[7] = 1; // DR
        positionIds[8] = 2; // DL
        positionIds[9] = 2; // DL
        positionIds[10] = 0; // DC
        positionIds[11] = 0; // DC
        positionIds[12] = 0; // DC
        positionIds[13] = 0; // DC
        positionIds[14] = 0; // DC
        positionIds[15] = 1; // DR
        positionIds[16] = 1; // DR
        positionIds[17] = 1; // DR
        positionIds[18] = 2; // DL
        positionIds[19] = 2; // DL
        positionIds[20] = 0; // DC
        positionIds[21] = 0; // DC
        positionIds[22] = 0; // DC
        positionIds[23] = 0; // DC
        positionIds[24] = 0; // DC
        positionIds[25] = 1; // DR
        positionIds[26] = 1; // DR
        positionIds[27] = 1; // DR
        positionIds[28] = 2; // DL
        positionIds[29] = 2; // DL
        positionIds[30] = 0; // DC
        positionIds[31] = 0; // DC
        positionIds[32] = 0; // DC
        positionIds[33] = 0; // DC
        positionIds[34] = 0; // DC
        positionIds[36] = 1; // DR
        positionIds[37] = 1; // DR
        positionIds[38] = 2; // DL
        positionIds[39] = 2; // DL
        positionIds[40] = 10; // DMC
        positionIds[41] = 10; // DMC
        positionIds[42] = 10; // DMC
        positionIds[43] = 10; // DMC
        positionIds[44] = 10; // DMC
        positionIds[45] = 11; // DMR
        positionIds[46] = 11; // DMR
        positionIds[47] = 11; // DMR
        positionIds[48] = 12; // DML
        positionIds[49] = 12; // DML
        positionIds[50] = 10; // DMC
        positionIds[51] = 10; // DMC
        positionIds[52] = 10; // DMC
        positionIds[53] = 10; // DMC
        positionIds[54] = 10; // DMC
        positionIds[55] = 11; // DMR
        positionIds[56] = 11; // DMR
        positionIds[57] = 11; // DMR
        positionIds[58] = 12; // DML
        positionIds[59] = 12; // DML
        positionIds[60] = 20; // AMC
        positionIds[61] = 20; // AMC
        positionIds[62] = 20; // AMC
        positionIds[63] = 20; // AMC
        positionIds[64] = 20; // AMC
        positionIds[65] = 21; // AMR
        positionIds[66] = 21; // AMR
        positionIds[67] = 21; // AMR
        positionIds[68] = 22; // AML
        positionIds[69] = 22; // AML
        positionIds[70] = 20; // AMC
        positionIds[71] = 20; // AMC
        positionIds[72] = 20; // AMC
        positionIds[73] = 20; // AMC
        positionIds[74] = 20; // AMC
        positionIds[75] = 21; // AMR
        positionIds[76] = 21; // AMR
        positionIds[77] = 21; // AMR
        positionIds[78] = 22; // AML
        positionIds[79] = 22; // AML
        positionIds[80] = 30; // FC
        positionIds[81] = 30; // FC
        positionIds[82] = 30; // FC
        positionIds[83] = 30; // FC
        positionIds[84] = 30; // FC
        positionIds[85] = 31; // FR
        positionIds[86] = 31; // FR
        positionIds[87] = 31; // FR
        positionIds[88] = 32; // FL
        positionIds[89] = 32; // FL
        positionIds[90] = 30; // FC
        positionIds[91] = 30; // FC
        positionIds[92] = 30; // FC
        positionIds[93] = 30; // FC
        positionIds[94] = 30; // FC
        positionIds[95] = 31; // FR
        positionIds[96] = 31; // FR
        positionIds[97] = 31; // FR
        positionIds[98] = 32; // FL
        positionIds[99] = 32; // FL
        positionIds[110] = 110; // GK

        layoutPositions[0][0] = 110; // 5-4-1 GK
        layoutPositions[0][1] = 1; // 5-4-1 DR
        layoutPositions[0][2] = 2; // 5-4-1 DL
        layoutPositions[0][3] = 0; // 5-4-1 DC
        layoutPositions[0][4] = 0; // 5-4-1 DC
        layoutPositions[0][5] = 0; // 5-4-1 DC
        layoutPositions[0][6] = 10; // 5-4-1 DMC
        layoutPositions[0][7] = 10; // 5-4-1 DMC
        layoutPositions[0][8] = 30; // 5-4-1 FC
        layoutPositions[0][9] = 21; // 5-4-1 AMR
        layoutPositions[0][10] = 22; // 5-4-1 AML
        layoutPositions[0][11] = 33; // 5-4-1 SUB
        layoutPositions[0][12] = 33; // 5-4-1 SUB
        layoutPositions[0][13] = 33; // 5-4-1 SUB
        layoutPositions[0][14] = 33; // 5-4-1 SUB
        layoutPositions[0][15] = 33; // 5-4-1 SUB

        layoutPositions[1][0] = 110; // 5-4-1* GK
        layoutPositions[1][2] = 1; // 5-4-1* DR
        layoutPositions[1][2] = 2; // 5-4-1* DL
        layoutPositions[1][3] = 0; // 5-4-1* DC
        layoutPositions[1][4] = 0; // 5-4-1* DC
        layoutPositions[1][5] = 0; // 5-4-1* DC
        layoutPositions[1][6] = 21; // 5-4-1* AMR
        layoutPositions[1][7] = 10; // 5-4-1* DMC
        layoutPositions[1][8] = 30; // 5-4-1* FC
        layoutPositions[1][9] = 20; // 5-4-1* AMC
        layoutPositions[1][10] = 22; // 5-4-1* AML
        layoutPositions[1][11] = 33; // 5-4-1* SUB
        layoutPositions[1][12] = 33; // 5-4-1* SUB
        layoutPositions[1][13] = 33; // 5-4-1* SUB
        layoutPositions[1][14] = 33; // 5-4-1* SUB
        layoutPositions[1][15] = 33; // 5-4-1* SUB

        layoutPositions[2][0] = 110; // 5-4-1** GK
        layoutPositions[2][1] = 1; // 5-4-1** DR
        layoutPositions[2][2] = 2; // 5-4-1** DL
        layoutPositions[2][3] = 0; // 5-4-1** DC
        layoutPositions[2][4] = 0; // 5-4-1** DC
        layoutPositions[2][5] = 0; // 5-4-1** DC
        layoutPositions[2][6] = 11; // 5-4-1** DMR
        layoutPositions[2][7] = 10; // 5-4-1** DMC
        layoutPositions[2][8] = 30; // 5-4-1** FC
        layoutPositions[2][9] = 20; // 5-4-1** AMC
        layoutPositions[2][10] = 12; // 5-4-1** DML
        layoutPositions[2][11] = 33; // 5-4-1* SUB
        layoutPositions[2][12] = 33; // 5-4-1** SUB
        layoutPositions[2][13] = 33; // 5-4-1** SUB
        layoutPositions[2][14] = 33; // 5-4-1** SUB
        layoutPositions[2][15] = 33; // 5-4-1** SUB

        layoutPositions[3][0] = 110; // 5-3-2 GK
        layoutPositions[3][1] = 1; // 5-3-2 DR
        layoutPositions[3][2] = 2; // 5-3-2 DL
        layoutPositions[3][3] = 0; // 5-3-2 DC
        layoutPositions[3][4] = 0; // 5-3-2 DC
        layoutPositions[3][5] = 0; // 5-3-2 DC
        layoutPositions[3][6] = 21; // 5-3-2 AMR
        layoutPositions[3][7] = 10; // 5-3-2 DMC
        layoutPositions[3][8] = 30; // 5-3-2 FC
        layoutPositions[3][9] = 22; // 5-3-2 AML
        layoutPositions[3][10] = 30; // 5-3-2 FC
        layoutPositions[3][11] = 33; // 5-3-2 SUB
        layoutPositions[3][12] = 33; // 5-3-2 SUB
        layoutPositions[3][13] = 33; // 5-3-2 SUB
        layoutPositions[3][14] = 33; // 5-3-2 SUB
        layoutPositions[3][15] = 33; // 5-3-2 SUB

        layoutPositions[4][0] = 110; // 5-3-2* GK
        layoutPositions[4][1] = 1; // 5-3-2* DR
        layoutPositions[4][2] = 2; // 5-3-2* DL
        layoutPositions[4][3] = 0; // 5-3-2* DC
        layoutPositions[4][4] = 0; // 5-3-2* DC
        layoutPositions[4][5] = 0; // 5-3-2* DC
        layoutPositions[4][6] = 10; // 5-3-2* DMC
        layoutPositions[4][7] = 10; // 5-3-2* DMC
        layoutPositions[4][8] = 31; // 5-3-2* FR
        layoutPositions[4][9] = 20; // 5-3-2* AMC
        layoutPositions[4][10] = 32; // 5-3-2* FL
        layoutPositions[4][11] = 33; // 5-3-2* SUB
        layoutPositions[4][12] = 33; // 5-3-2* SUB
        layoutPositions[4][13] = 33; // 5-3-2* SUB
        layoutPositions[4][14] = 33; // 5-3-2* SUB
        layoutPositions[4][15] = 33; // 5-3-2* SUB

        layoutPositions[5][0] = 110; // 4-5-1 GK
        layoutPositions[5][1] = 1; // 4-5-1 DR
        layoutPositions[5][2] = 2; // 4-5-1 DL
        layoutPositions[5][3] = 0; // 4-5-1 DC
        layoutPositions[5][4] = 0; // 4-5-1 DC
        layoutPositions[5][5] = 10; // 4-5-1 DMC
        layoutPositions[5][6] = 21; // 4-5-1 AMR
        layoutPositions[5][7] = 10; // 4-5-1 DMC
        layoutPositions[5][8] = 30; // 4-5-1 FC
        layoutPositions[5][9] = 20; // 4-5-1 AMC
        layoutPositions[5][10] = 22; // 4-5-1 AML
        layoutPositions[5][11] = 33; // 4-5-1 SUB
        layoutPositions[5][12] = 33; // 4-5-1 SUB
        layoutPositions[5][13] = 33; // 4-5-1 SUB
        layoutPositions[5][14] = 33; // 4-5-1 SUB
        layoutPositions[5][15] = 33; // 4-5-1 SUB

        layoutPositions[6][0] = 110; // 4-5-1* GK
        layoutPositions[6][1] = 1; // 4-5-1* DR
        layoutPositions[6][2] = 2; // 4-5-1* DL
        layoutPositions[6][3] = 0; // 4-5-1* DC
        layoutPositions[6][4] = 0; // 4-5-1* DC
        layoutPositions[6][5] = 10; // 4-5-1* DMC
        layoutPositions[6][6] = 11; // 4-5-1* DMR
        layoutPositions[6][7] = 12; // 4-5-1* DML
        layoutPositions[6][8] = 30; // 4-5-1* FC
        layoutPositions[6][9] = 20; // 4-5-1* AMC
        layoutPositions[6][10] = 20; // 4-5-1* AMC
        layoutPositions[6][11] = 33; // 4-5-1* SUB
        layoutPositions[6][12] = 33; // 4-5-1* SUB
        layoutPositions[6][13] = 33; // 4-5-1* SUB
        layoutPositions[6][14] = 33; // 4-5-1* SUB
        layoutPositions[6][15] = 33; // 4-5-1* SUB

        layoutPositions[7][0] = 110; // 4-4-2 GK
        layoutPositions[7][1] = 1; // 4-4-2 DR
        layoutPositions[7][2] = 2; // 4-4-2 DL
        layoutPositions[7][3] = 0; // 4-4-2 DC
        layoutPositions[7][4] = 0; // 4-4-2 DC
        layoutPositions[7][5] = 10; // 4-4-2 DMC
        layoutPositions[7][6] = 21; // 4-4-2 AMR
        layoutPositions[7][7] = 10; // 4-4-2 DMC
        layoutPositions[7][8] = 30; // 4-4-2 FC
        layoutPositions[7][9] = 22; // 4-4-2 AML
        layoutPositions[7][10] = 30; // 4-4-2 FC
        layoutPositions[7][11] = 33; // 4-4-2 SUB
        layoutPositions[7][12] = 33; // 4-4-2 SUB
        layoutPositions[7][13] = 33; // 4-4-2 SUB
        layoutPositions[7][14] = 33; // 4-4-2 SUB
        layoutPositions[7][15] = 33; // 4-4-2 SUB

        layoutPositions[8][0] = 110; // 4-4-2* GK
        layoutPositions[8][1] = 1; // 4-4-2* DR
        layoutPositions[8][2] = 2; // 4-4-2* DL
        layoutPositions[8][3] = 0; // 4-4-2* DC
        layoutPositions[8][4] = 0; // 4-4-2* DC
        layoutPositions[8][5] = 10; // 4-4-2* DMC
        layoutPositions[8][6] = 11; // 4-4-2* DMR
        layoutPositions[8][7] = 12; // 4-4-2* DML
        layoutPositions[8][8] = 31; // 4-4-2* FR
        layoutPositions[8][9] = 20; // 4-4-2* AMC
        layoutPositions[8][10] = 30; // 4-4-2* FL
        layoutPositions[8][11] = 33; // 4-4-2* SUB
        layoutPositions[8][12] = 33; // 4-4-2* SUB
        layoutPositions[8][13] = 33; // 4-4-2* SUB
        layoutPositions[8][14] = 33; // 4-4-2* SUB
        layoutPositions[8][15] = 33; // 4-4-2* SUB

        layoutPositions[9][0] = 110; // 4-3-3 GK
        layoutPositions[9][1] = 1; // 4-3-3 DR
        layoutPositions[9][2] = 2; // 4-3-3 DL
        layoutPositions[9][3] = 0; // 4-3-3 DC
        layoutPositions[9][4] = 0; // 4-3-3 DC
        layoutPositions[9][5] = 11; // 4-3-3 DMR
        layoutPositions[9][6] = 31; // 4-3-3 FR
        layoutPositions[9][7] = 12; // 4-3-3 DML
        layoutPositions[9][8] = 30; // 4-3-3 FC
        layoutPositions[9][9] = 20; // 4-3-3 AMC
        layoutPositions[9][10] = 32; // 4-3-3 FL
        layoutPositions[9][11] = 33; // 4-3-3 SUB
        layoutPositions[9][12] = 33; // 4-3-3 SUB
        layoutPositions[9][13] = 33; // 4-3-3 SUB
        layoutPositions[9][14] = 33; // 4-3-3 SUB
        layoutPositions[9][15] = 33; // 4-3-3 SUB

        layoutPositions[10][0] = 110; // 4-3-3* GK
        layoutPositions[10][1] = 1; // 4-3-3* DR
        layoutPositions[10][2] = 2; // 4-3-3* DL
        layoutPositions[10][3] = 0; // 4-3-3* DC
        layoutPositions[10][4] = 0; // 4-3-3* DC
        layoutPositions[10][5] = 10; // 4-3-3* DMC
        layoutPositions[10][6] = 31; // 4-3-3* FR
        layoutPositions[10][7] = 20; // 4-3-3* AMC
        layoutPositions[10][8] = 30; // 4-3-3* FC
        layoutPositions[10][9] = 20; // 4-3-3* AMC
        layoutPositions[10][10] = 32; // 4-3-3* FL
        layoutPositions[10][11] = 33; // 4-3-3* SUB
        layoutPositions[10][12] = 33; // 4-3-3* SUB
        layoutPositions[10][13] = 33; // 4-3-3* SUB
        layoutPositions[10][14] = 33; // 4-3-3* SUB
        layoutPositions[10][15] = 33; // 4-3-3* SUB

        layoutPositions[11][0] = 110; // 3-5-2 GK
        layoutPositions[11][1] = 0; // 3-5-2 DC
        layoutPositions[11][2] = 0; // 3-5-2 DC
        layoutPositions[11][3] = 0; // 3-5-2 DC
        layoutPositions[11][4] = 11; // 3-5-2 DMR
        layoutPositions[11][5] = 10; // 3-5-2 DMC
        layoutPositions[11][6] = 20; // 3-5-2 AMC
        layoutPositions[11][7] = 12; // 3-5-2 DML
        layoutPositions[11][8] = 30; // 3-5-2 FC
        layoutPositions[11][9] = 20; // 3-5-2 AMC
        layoutPositions[11][10] = 30; // 3-5-2 FC
        layoutPositions[11][11] = 33; // 3-5-2 SUB
        layoutPositions[11][12] = 33; // 3-5-2 SUB
        layoutPositions[11][13] = 33; // 3-5-2 SUB
        layoutPositions[11][14] = 33; // 3-5-2 SUB
        layoutPositions[11][15] = 33; // 3-5-2 SUB

        layoutPositions[12][0] = 110; // 3-5-2* GK
        layoutPositions[12][1] = 0; // 3-5-2* DC
        layoutPositions[12][2] = 0; // 3-5-2* DC
        layoutPositions[12][3] = 0; // 3-5-2* DC
        layoutPositions[12][4] = 10; // 3-5-2* DMC
        layoutPositions[12][5] = 10; // 3-5-2* DMC
        layoutPositions[12][6] = 21; // 3-5-2* AMR
        layoutPositions[12][7] = 22; // 3-5-2* AML
        layoutPositions[12][8] = 30; // 3-5-2* FC
        layoutPositions[12][9] = 20; // 3-5-2* AMC
        layoutPositions[12][10] = 30; // 3-5-2* FC
        layoutPositions[12][11] = 33; // 3-5-2* SUB
        layoutPositions[12][12] = 33; // 3-5-2* SUB
        layoutPositions[12][13] = 33; // 3-5-2* SUB
        layoutPositions[12][14] = 33; // 3-5-2* SUB
        layoutPositions[12][15] = 33; // 3-5-2* SUB

        layoutPositions[13][0] = 110; // 3-4-3 GK
        layoutPositions[13][1] = 0; // 3-4-3 DC
        layoutPositions[13][2] = 0; // 3-4-3 DC
        layoutPositions[13][3] = 0; // 3-4-3 DC
        layoutPositions[13][4] = 11; // 3-4-3 DMR
        layoutPositions[13][5] = 10; // 3-4-3 DMC
        layoutPositions[13][6] = 31; // 3-4-3 FR
        layoutPositions[13][7] = 12; // 3-4-3 DML
        layoutPositions[13][8] = 30; // 3-4-3 FC
        layoutPositions[13][9] = 20; // 3-4-3 AMC
        layoutPositions[13][10] = 32; // 3-4-3 FL
        layoutPositions[13][11] = 33; // 3-4-3 SUB
        layoutPositions[13][12] = 33; // 3-4-3 SUB
        layoutPositions[13][13] = 33; // 3-4-3 SUB
        layoutPositions[13][14] = 33; // 3-4-3 SUB
        layoutPositions[13][15] = 33; // 3-4-3 SUB
    }

    function signUpPlayer(
        uint16 _playerId,
        uint256 _teamId,
        uint256 _gameId,
        uint8 _position
    ) external onlyPlayerOwner(_playerId) {
        if (leagueTeam.playersTeam(_playerId) != _teamId) revert NotInTeam();
        if (isPlayerSignedUp[_playerId] == true) revert AlreadySigned();
        if (
            ((leagueGame.games(_gameId, 1) == _teamId && _position < 16) ||
                (leagueGame.games(_gameId, 2) == _teamId &&
                    _position > 15 &&
                    _position < 32)) != true
        ) revert IncorrectGameTeamPosition();
        if (
            block.number < leagueGame.games(_gameId, 0) - preRegistration ||
            block.number > leagueGame.games(_gameId, 0) + gameDuration
        ) revert NoCurrentGame();
        if (gamePlayers[_gameId][_position].playerId > 0)
            revert PositionNotAvailable();
        playerSignUp memory _playerSignUp;
        _playerSignUp.playerId = _playerId;
        _playerSignUp.blockSigned = block.number;
        gamePlayers[_gameId][_position] = _playerSignUp; // Register the player for the game, in his team and position
        isPlayerSignedUp[_playerId] = true; // Flag the players as signed up to avoid that a player signs for several positions in the same game
        emit playerSignedUp(_gameId, _playerId, _position);
    }

    function setPlayerRates(uint256 _gameId) external returns (bool success) {
        uint256 _gameStart = leagueGame.games(_gameId, 0);
        if (_gameStart + gameDuration > block.number)
            revert TooEarly(block.number, _gameStart + gameDuration);
        uint256 _teamId = leagueGame.games(_gameId, 1);
        uint256 _layoutId = leagueGame.teamGame(_teamId, 2);

        uint8 _subsCount;
        // Count the substitutes of home team
        for (uint8 i = 11; i < 16; i++) {
            if (gamePlayers[_gameId][i].playerId > 0) {
                _subsCount++;
            }
        }
        // Loop through the home team players
        for (uint8 i = 0; i < 11; i++) {
            uint16 _playerId = gamePlayers[_gameId][i].playerId;
            uint8 _bonus = 0;

            // Bonus for home team
            _bonus += 1;
            if (leagueTeam.teamMembers(_teamId, 1) == _playerId) {
                // Bonus for captain
                _bonus += 1;
            }
            if (
                layoutPositions[_layoutId][i] ==
                positionIds[
                    verifiableRandomFootballer.tokenIdToAttributes(_playerId, 0)
                ]
            ) {
                // Bonus for preferred position
                _bonus += 2;
            } else if (
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 1) ||
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 2) ||
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 3)
            ) {
                // Bonus for compatible position
                _bonus += 1;
            }
            if (_subsCount > 2) {
                // Bonus for at least 3 three subs
                _bonus += 1;
            }
            if (_subsCount > 4) {
                // Bonus for 5 subs
                _bonus += 1;
            }
            if (gamePlayers[_playerId][i].blockSigned < _gameStart) {
                // Penalty for too early sign up
                if (_bonus < 2) {
                    _bonus = 0;
                } else {
                    _bonus -= 2;
                }
            } else if (
                gamePlayers[_playerId][i].blockSigned - _gameStart <
                gameDuration / 6
            ) {
                // Bonus for early sign up
                _bonus += 2;
            } else if (
                gamePlayers[_playerId][i].blockSigned - _gameStart <
                gameDuration / 2
            ) {
                // Bonus for first half sign up
                _bonus += 1;
            }
            if (
                _gameStart - leagueGame.games(playerLastGame[_playerId], 0) <
                durationBetweenGames
            ) {
                // Penalty for not enough time between two games
                if (_bonus < 2) {
                    _bonus = 0;
                } else {
                    _bonus -= 2;
                }
            }
            if (
                _gameStart - leagueGame.games(playerLastGame[_playerId], 0) >
                4 * durationBetweenGames
            ) {
                // Penalty for two much time between two games
                if (_bonus < 1) {
                    _bonus = 0;
                } else {
                    _bonus -= 1;
                }
            }
            if (
                _gameStart - leagueGame.games(playerLastGame[_playerId], 0) >
                8 * durationBetweenGames
            ) {
                // Penalty for two much time between two games
                if (_bonus < 2) {
                    _bonus = 0;
                } else {
                    _bonus -= 2;
                }
            }
            if (
                leagueGame.teamGame(_teamId, 3) >
                leagueGame.teamGame(leagueGame.games(_gameId, 2), 3)
            ) {
                // Bonus for higher team stake
                _bonus += 2;
            }

            if (_bonus > 10) _bonus = 10;

            playerSignUp memory _playerSignUp;
            _playerSignUp.playerId = _playerId;
            _playerSignUp.blockSigned = gamePlayers[_playerId][i].blockSigned;
            _playerSignUp.defenseRate =
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 4) +
                _bonus;
            _playerSignUp.attackRate =
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 5) +
                _bonus;

            gamePlayers[_gameId][i] = _playerSignUp; // Saves the player to calculate their goals scored in the GameResult Contract
            playerLastGame[_playerId] = _gameId; // Save the game as last player game to calculate the duration between two games in which the player participated
            isPlayerSignedUp[_playerId] = false; // Liberates the player to participate in another game
        }
        _subsCount = 0;
        _teamId = leagueGame.games(_gameId, 2);
        _layoutId = leagueGame.teamGame(_teamId, 2);

        // Count the substitutes of away team
        for (uint8 i = 27; i < 31; i++) {
            if (gamePlayers[_gameId][i].playerId > 0) {
                _subsCount++;
            }
        }
        // Loop on the away team players
        for (uint8 j = 16; j < 27; j++) {
            uint8 i = j - 16;
            uint16 _playerId = gamePlayers[_gameId][j].playerId;
            uint8 _bonus = 0;

            if (leagueTeam.teamMembers(_teamId, 1) == _playerId) {
                // Bonus for captain
                _bonus += 1;
            }
            if (
                layoutPositions[_layoutId][i] ==
                positionIds[
                    verifiableRandomFootballer.tokenIdToAttributes(_playerId, 0)
                ]
            ) {
                // Bonus for preferred position
                _bonus += 2;
            } else if (
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 1) ||
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 2) ||
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 3)
            ) {
                // Bonus for compatible position
                _bonus += 1;
            }
            if (_subsCount > 2) {
                // Bonus for at least 3 three subs
                _bonus += 1;
            }
            if (_subsCount > 4) {
                // Bonus for 5 subs
                _bonus += 1;
            }
            if (gamePlayers[_gameId][j].blockSigned < _gameStart) {
                // Penalty for too early sign up
                if (_bonus < 2) {
                    _bonus = 0;
                } else {
                    _bonus -= 2;
                }
            } else if (
                gamePlayers[_gameId][j].blockSigned - _gameStart <
                gameDuration / 6
            ) {
                // Bonus for early sign up
                _bonus += 2;
            } else if (
                gamePlayers[_gameId][j].blockSigned - _gameStart <
                gameDuration / 2
            ) {
                // Bonus for first half sign up
                _bonus += 1;
            }
            if (
                _gameStart - leagueGame.games(playerLastGame[_playerId], 0) <
                durationBetweenGames
            ) {
                // Penalty for not enough time between two games
                if (_bonus < 2) {
                    _bonus = 0;
                } else {
                    _bonus -= 2;
                }
            }
            if (
                _gameStart - leagueGame.games(playerLastGame[_playerId], 0) >
                4 * durationBetweenGames
            ) {
                // Penalty for two much time between two games
                if (_bonus < 1) {
                    _bonus = 0;
                } else {
                    _bonus -= 1;
                }
            }
            if (
                _gameStart - leagueGame.games(playerLastGame[_playerId], 0) >
                8 * durationBetweenGames
            ) {
                // Penalty for two much time between two games
                if (_bonus < 2) {
                    _bonus = 0;
                } else {
                    _bonus -= 2;
                }
            }
            if (
                leagueGame.teamGame(_teamId, 3) >
                leagueGame.teamGame(leagueGame.games(_gameId, 1), 3)
            ) {
                // Bonus for higher team stake
                _bonus += 2;
            }

            playerSignUp memory _playerSignUp;
            _playerSignUp.playerId = _playerId;
            _playerSignUp.blockSigned = gamePlayers[_gameId][j].blockSigned;
            _playerSignUp.defenseRate =
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 4) +
                _bonus;
            _playerSignUp.attackRate =
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 5) +
                _bonus;

            gamePlayers[_gameId][j] = _playerSignUp; // Saves the player to calculate their goals scored in the GameResult Contract
            playerLastGame[_playerId] = _gameId; // Save the game as last player game to calculate the duration between two games in which the player participated
            isPlayerSignedUp[_playerId] = false; // Liberates the player to participate in another game
        }
        return true;
    }

    function setGameDuration(uint256 _duration) public onlyOwner {
        gameDuration = _duration;
        emit updateGameDuration(_duration);
    }

    function setDurationBetweenGames(uint256 _duration) public onlyOwner {
        durationBetweenGames = _duration;
        emit updateDurationBetweenGames(_duration);
    }

    function setPreRegistration(uint256 _duration) public onlyOwner {
        preRegistration = _duration;
        emit updatePreRegistration(_duration);
    }
}
