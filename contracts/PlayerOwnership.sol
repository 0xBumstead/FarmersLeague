//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../interfaces/IVerifiableRandomFootballer.sol";
import "../interfaces/IPlayerLoan.sol";

contract PlayerOwnership {
    IPlayerLoan internal playerLoan;
    IVerifiableRandomFootballer internal verifiableRandomFootballer;

    error NotOwner(address sender, address owner);

    constructor(address _playerLoan, address _verifiableRandomFootballer) {
        playerLoan = IPlayerLoan(_playerLoan);
        verifiableRandomFootballer = IVerifiableRandomFootballer(
            _verifiableRandomFootballer
        );
    }

    // used to consider the loans on top of real NFT ownership
    function currentOwner(uint16 _playerId)
        public
        view
        returns (address owner)
    {
        (address _borrower, uint256 _term) = playerLoan.loans(_playerId);
        if (_term < block.number) {
            owner = verifiableRandomFootballer.ownerOf(_playerId);
        } else {
            owner = _borrower;
        }
    }

    modifier onlyPlayerOwner(uint16 _playerId) {
        if (currentOwner(_playerId) != msg.sender)
            revert NotOwner(msg.sender, currentOwner(_playerId));
        _;
    }
}
