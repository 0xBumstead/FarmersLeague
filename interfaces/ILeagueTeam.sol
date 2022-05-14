// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface ILeagueTeam {
    function teamCreationPrice() external view returns (uint256 price);

    function releasePrice() external view returns (uint256 price);

    function playersTeam(uint16 _playerId)
        external
        view
        returns (uint256 teamId);

    function teamMembers(uint256 _teamId, uint256 _position)
        external
        view
        returns (uint16 member);

    function playersApplication(uint16 _playerId)
        external
        view
        returns (uint256 teamId);

    function teamApplications(uint256 _teamId, uint256 _position)
        external
        view
        returns (uint16 application);

    function createTeam(uint16 _captainId)
        external
        payable
        returns (bool success);

    function removeTeam(uint256 _teamId) external returns (bool success);

    function applyForTeam(uint16 _playerId, uint256 _teamId)
        external
        returns (bool success);

    function cancelApplication(uint16 _playerId, uint256 _teamId)
        external
        returns (bool success);

    function validateApplication(uint16 _playerId, uint256 _teamId)
        external
        returns (bool successs);

    function clearApplications(uint256 _teamId) external returns (bool success);

    function releasePlayer(uint16 _playerId, uint256 _teamId)
        external
        returns (bool success);

    function payReleaseClause(uint16 _playerId)
        external
        payable
        returns (bool success);
}
