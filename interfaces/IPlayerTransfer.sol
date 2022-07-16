// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IPlayerTransfer {
    function playersForTransfer(uint16 _playerId)
        external
        view
        returns (uint256 price);

    function transferList() external view returns (uint16[] memory playerIds);

    function listPlayerForTransfer(uint256 _price, uint16 _playerId)
        external
        returns (bool success);

    function unlistPlayer(uint16 _playerId) external returns (bool success);

    function transfer(uint16 _playerId) external returns (bool success);

    function withdraw() external returns (bool successs);
}
