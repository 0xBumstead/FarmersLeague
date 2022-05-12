// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IGameResult {
    function setResult(uint256 _gameId) external returns (uint8 result);
}
