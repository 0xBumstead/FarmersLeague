// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./PlayerOwnership.sol";
import "../interfaces/ILeagueTeam.sol";
import "../interfaces/ILeagueGame.sol";
import "./PlayerOwnership.sol";
import "./UnsafeMath.sol";

error TooEarly(uint256 time, uint256 requested);
error NotInTeam();
error AlreadySigned();
error IncorrectGameTeamPosition();
error NoCurrentGame();
error PositionNotAvailable();

contract PlayerRate is Ownable, PlayerOwnership {
    using UnsafeMath8 for uint8;

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
    event playerSignedUp(
        uint256 indexed gameId,
        uint16 indexed playerId,
        uint8 position
    );
    event positionStored(uint8 positionId, uint8 positionCode);
    event layoutStored(uint8 layoutId, uint8[16] layoutPositions);

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
        for (uint8 i = 11; i < 16; i = i.unsafe_increment()) {
            if (gamePlayers[_gameId][i].playerId > 0) {
                _subsCount = _subsCount.unsafe_increment();
            }
        }
        // Loop through the home team players
        for (uint8 i = 0; i < 11; i = i.unsafe_increment()) {
            uint16 _playerId = gamePlayers[_gameId][i].playerId;
            uint8 _bonus = 0;

            // Bonus for home team
            _bonus = _bonus.unsafe_increment();
            if (leagueTeam.teamMembers(_teamId, 1) == _playerId) {
                // Bonus for captain
                _bonus = _bonus.unsafe_increment();
            }
            if (
                layoutPositions[_layoutId][i] ==
                positionIds[
                    verifiableRandomFootballer.tokenIdToAttributes(_playerId, 0)
                ]
            ) {
                // Bonus for preferred position
                _bonus = UnsafeMath8.unsafe_add(_bonus, 2);
            } else if (
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 1) ||
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 2) ||
                layoutPositions[_layoutId][i] ==
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 3)
            ) {
                // Bonus for compatible position
                _bonus = _bonus.unsafe_increment();
            }
            if (_subsCount > 2) {
                // Bonus for at least 3 three subs
                _bonus = _bonus.unsafe_increment();
            }
            if (_subsCount > 4) {
                // Bonus for 5 subs
                _bonus = _bonus.unsafe_increment();
            }
            if (gamePlayers[_playerId][i].blockSigned < _gameStart) {
                // Penalty for too early sign up
                if (_bonus < 2) {
                    _bonus = 0;
                } else {
                    _bonus = UnsafeMath8.unsafe_sub(_bonus, 2);
                }
            } else if (
                gamePlayers[_playerId][i].blockSigned - _gameStart <
                gameDuration / 6
            ) {
                // Bonus for early sign up
                _bonus = UnsafeMath8.unsafe_add(_bonus, 2);
            } else if (
                gamePlayers[_playerId][i].blockSigned - _gameStart <
                gameDuration / 2
            ) {
                // Bonus for first half sign up
                _bonus = _bonus.unsafe_increment();
            }
            if (
                _gameStart - leagueGame.games(playerLastGame[_playerId], 0) <
                durationBetweenGames
            ) {
                // Penalty for not enough time between two games
                if (_bonus < 2) {
                    _bonus = 0;
                } else {
                    _bonus = UnsafeMath8.unsafe_sub(_bonus, 2);
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
                    _bonus = _bonus.unsafe_decrement();
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
                    _bonus = UnsafeMath8.unsafe_sub(_bonus, 2);
                }
            }
            if (
                leagueGame.teamGame(_teamId, 3) >
                leagueGame.teamGame(leagueGame.games(_gameId, 2), 3)
            ) {
                // Bonus for higher team stake
                _bonus = UnsafeMath8.unsafe_add(_bonus, 2);
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
            _playerSignUp.defenseRate = UnsafeMath8.unsafe_add(
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 4),
                _bonus
            );
            _playerSignUp.attackRate = UnsafeMath8.unsafe_add(
                verifiableRandomFootballer.tokenIdToAttributes(_playerId, 5),
                _bonus
            );

            gamePlayers[_gameId][j] = _playerSignUp; // Saves the player to calculate their goals scored in the GameResult Contract
            playerLastGame[_playerId] = _gameId; // Save the game as last player game to calculate the duration between two games in which the player participated
            isPlayerSignedUp[_playerId] = false; // Liberates the player to participate in another game
        }
        return true;
    }

    function getGamePlayers(uint256 _gameId)
        external
        view
        returns (playerSignUp[32] memory players)
    {
        return gamePlayers[_gameId];
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

    function storePosition(uint8 _positionId, uint8 _positionCode)
        public
        onlyOwner
    {
        positionIds[_positionId] = _positionCode;
        emit positionStored(_positionId, _positionCode);
    }

    function storeLayout(uint8 _layoutId, uint8[16] calldata _positions)
        public
        onlyOwner
    {
        for (uint8 i = 0; i < 16; i = i.unsafe_increment()) {
            layoutPositions[_layoutId][i] = _positions[i];
        }
        emit layoutStored(_layoutId, _positions);
    }
}
