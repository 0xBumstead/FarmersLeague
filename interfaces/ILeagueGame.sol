// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface ILeagueGame {
    function gameIds() external view returns (uint256 numberOfGames);

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

    function teamChallenge(
        uint256 _challengedTeamId,
        uint256 _challengingTeamId
    ) external view returns (uint256 challengeDeadLine);

    function requestIdToGameId(bytes32 _requestId)
        external
        view
        returns (uint256 requestIdToGameId);

    function signUpTeam(
        uint256 _teamId,
        uint256 _layout,
        uint256 _stake
    ) external payable returns (bool success);

    function cancelSignUp(uint256 _teamId) external returns (bool success);

    function challengeTeam(uint256 _teamId, uint256 _opponentTeamId)
        external
        returns (bool success);

    function declineChallenge(uint256 _teamId, uint256 _opponentTeamId)
        external
        returns (bool success);

    function requestGame(uint256 _teamId, uint256 _opponentTeamId)
        external
        returns (bytes32 requestId);

    function finishGame(uint256 _gameId) external returns (bool success);
}
