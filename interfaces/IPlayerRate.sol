// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IPlayerRate {
    struct playerSignUp {
        uint16 playerId;
        uint256 blockSigned;
        uint8 defenseRate;
        uint8 attackRate;
    }

    function gameDuration() external view returns (uint256 time);

    function durationBetweenGames() external view returns (uint256 time);

    function preRegistration() external view returns (uint256 time);

    function gamePlayers(uint256 _gameId, uint256 _rank)
        external
        view
        returns (
            uint16 playerId,
            uint256 blockSigned,
            uint8 defenseRate,
            uint8 attackRate
        );

    function playerLastGame(uint16 _playerId)
        external
        view
        returns (uint256 time);

    function isPlayerSignedUp(uint16 _playerId)
        external
        view
        returns (bool signed);

    function positionIds(uint8 _position)
        external
        view
        returns (uint8 positionId);

    function layoutPositions(uint256 _layoutId, uint8 _position)
        external
        view
        returns (uint8 positionId);

    function signUpPlayer(
        uint16 _playerId,
        uint256 _teamId,
        uint256 _gameId,
        uint8 _position
    ) external returns (bool success);

    function getGamePlayers(uint256 _gameId)
        external
        view
        returns (playerSignUp[32] memory players);

    function setPlayerRates(uint256 _gameId) external returns (bool success);
}
