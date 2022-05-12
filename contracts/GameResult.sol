// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../interfaces/IPlayerRate.sol";
import "../interfaces/ILeagueGame.sol";

contract GameResult {
    IPlayerRate internal playerRate;
    ILeagueGame internal leagueGame;

    constructor(address _playerRate, address _leagueGame) {
        playerRate = IPlayerRate(_playerRate);
        leagueGame = ILeagueGame(_leagueGame);
    }

    // function called by the finishGame function of the leagueGame contract
    function setResult(uint256 _gameId) external returns (uint8 result) {
        bool _ratesCalculated = playerRate.setPlayerRates(_gameId);
        if (_ratesCalculated) {
            uint8 _homeGoals = scoreGoals(_gameId, true);
            uint8 _awayGoals = scoreGoals(_gameId, false);
            if (_homeGoals > _awayGoals) {
                result = 1;
            } else if (_homeGoals < _awayGoals) {
                result = 2;
            } else {
                result = 3;
            }
        }
    }

    // Calculates the number of goals of a team in a game based on the attack ratings of the team players and the defense Avg rating of the opponent
    function scoreGoals(uint256 _gameId, bool _isHome)
        internal
        view
        returns (uint8 goals)
    {
        uint256 _defenseAvg = teamAvgRates(_gameId, !_isHome);
        uint8 _collectiveGoal = 0;
        if (_isHome) {
            // Loop through the layout positions to check if the player signed up to the position gets a goal
            for (uint256 i = 0; i < 11; ++i) {
                (, , , uint8 _attackRate) = playerRate.gamePlayers(_gameId, i);
                if (_attackRate > _defenseAvg + 3) {
                    goals++; // player gets an individual goal
                } else if (_attackRate > _defenseAvg + 1) {
                    _collectiveGoal++; // player can participate in a collective goal
                }
                if (_collectiveGoal == 3) {
                    goals++; // 3 players are eligibles so the team gets a collective goal
                    _collectiveGoal = 0;
                }
            }
        } else {
            // Same thing than above but for the away team positions
            for (uint256 i = 16; i < 27; ++i) {
                (, , , uint8 _attackRate) = playerRate.gamePlayers(_gameId, i);
                if (_attackRate > _defenseAvg + 3) {
                    goals++;
                } else if (_attackRate > _defenseAvg + 1) {
                    _collectiveGoal++;
                }
                if (_collectiveGoal == 3) {
                    goals++;
                    _collectiveGoal = 0;
                }
            }
        }
    }

    // Calculates the defense average ratings of the 11 players of a team
    function teamAvgRates(uint256 _gameId, bool _isHome)
        internal
        view
        returns (uint256 defenseAvg)
    {
        uint8 _players = 0;
        if (_isHome) {
            // Loop through the layout positions
            for (uint256 i = 0; i < 11; ++i) {
                (uint16 _playerId, , uint8 _defenseRate, ) = playerRate
                    .gamePlayers(_gameId, i);
                // Check if the position is occupied by a signed up player
                if (_playerId > 0) {
                    defenseAvg = defenseAvg + _defenseRate;
                    _players++;
                }
            }
        } else {
            for (uint256 i = 16; i < 27; ++i) {
                // Same thing than above but for the away team positions
                (uint16 _playerId, , , uint8 _defenseRate) = playerRate
                    .gamePlayers(_gameId, i);
                if (_playerId > 0) {
                    defenseAvg = defenseAvg + _defenseRate;
                    _players++;
                }
            }
        }
        if (_players > 0) {
            if (_players < 8) _players = 8; // The average is calculated on at least 8 players (the non signed up players are considered at 0 defense rate)
            defenseAvg = (defenseAvg * 10**18) / _players; // handle the decimals on the average
        } else {
            defenseAvg = 0;
        }
    }
}
