// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IPlayerLoan {
    function playersForLoan(uint16 _playerId)
        external
        view
        returns (uint256 duration, uint256 price);

    function loans(uint16 _playerId)
        external
        view
        returns (address borrower, uint256 term);

    function listPlayerForLoan(
        uint256 _duration,
        uint256 _price,
        uint16 _playerId
    ) external returns (bool success);

    function unlistPlayer(uint16 _playerId) external returns (bool success);

    function loan(uint16 _playerId) external returns (bool success);

    function withdraw() external returns (bool successs);
}
