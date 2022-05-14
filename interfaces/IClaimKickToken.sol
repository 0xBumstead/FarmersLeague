// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IClaimKickToken {
    function NFTClaim(uint16 _playerId) external view returns (bool claimed);

    function claim(uint16 _playerId) external returns (bool success);

    function withdraw() external returns (bool success);
}
