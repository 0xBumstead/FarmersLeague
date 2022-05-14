// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

error NotOwner(address sender, address owner);
error AlreadyClaimed();
error ContractBalanceTooLow(uint256 contractBalance);

contract ClaimKickToken is Ownable, ReentrancyGuard {
    IERC20 internal kickToken;
    IERC721 internal verifiableRandomFootballer;

    mapping(uint16 => bool) public NFTClaim; // Keep track of the NFT that has already claimed their tokens

    event tokenClaimed(uint16 tokenId);

    constructor(address _kickToken, address _VerifiableRandomFootballer) {
        kickToken = IERC20(_kickToken);
        verifiableRandomFootballer = IERC721(_VerifiableRandomFootballer);
    }

    // Allows each owner of 1 of the 10,000 NFT to claim 100 KICK, but only one time per NFT
    function claim(uint16 _tokenId) external nonReentrant {
        if (verifiableRandomFootballer.ownerOf(_tokenId) != msg.sender)
            revert NotOwner(
                msg.sender,
                verifiableRandomFootballer.ownerOf(_tokenId)
            );
        if (NFTClaim[_tokenId] == true) revert AlreadyClaimed();
        if (kickToken.balanceOf(address(this)) < 100 * 10**18)
            revert ContractBalanceTooLow(kickToken.balanceOf(address(this)));
        NFTClaim[_tokenId] = true;
        kickToken.transfer(msg.sender, 100 * 10**18);
        emit tokenClaimed(_tokenId);
    }

    function withdraw() external payable onlyOwner {
        kickToken.transfer(msg.sender, kickToken.balanceOf(address(this)));
    }
}
