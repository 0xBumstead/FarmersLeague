// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

interface IVerifiableRandomFootballer is IERC721 {
    function tokenIdToAttributes(uint16 _tokenId, uint256 _position)
        external
        view
        returns (uint8 attribute);
}
