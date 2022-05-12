// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface ILeagueGame {
    function prices(uint256 _rank) external view returns (uint256 price);

    function challengeTime() external view returns (uint256 time);

    function gameDelay(uint256 _rank) external view returns (uint256 delay);

    function teamGame(uint256 _teamId, uint256 _rank)
        external
        view
        returns (uint256 teamGameData);

    function games(uint256 _gameId, uint256 _rank)
        external
        view
        returns (uint256 gameData);

    function teamChallenge(uint256 _firstTeamId, uint256 _secondTeamId)
        external
        view
        returns (uint256 _teamChallenge);

    function requestIdToGameId(bytes32 _requestId)
        external
        view
        returns (uint256 _requestIdToGameId);

    function signUpTeam(uint256 _teamId, uint256 _layout)
        external
        returns (bool success);

    function challengeTeam(uint256 _teamId, uint256 _opponentTeamId)
        external
        returns (bool success);

    function declineChallenge(uint256 _teamId, uint256 _opponentTeamId)
        external
        returns (bool success);

    function requestGame(uint256 _teamId, uint256 _opponentTeamId)
        external
        returns (bytes32 requestId);

    function finishGame(uint256 _gameId, uint8 _result)
        external
        returns (bool success);
}
