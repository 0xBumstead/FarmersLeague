// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

error NotOwner(address sender, address owner);
error AlreadyListed();
error NotListed();
error AlreadyOnLoan();
error BalanceTooLow(uint256 balance, uint256 requested);
error MaxDuration(uint256 duration, uint256 maximum);

contract PlayerLoan is Ownable, ReentrancyGuard {
    IERC20 public kickToken;
    IERC721 public verifiableRandomFootballer;

    struct LoanTerm {
        address borrower;
        uint256 term;
    }
    mapping(uint16 => uint256[2]) public playersForLoan; // Mapping of tokenId to duration and price
    mapping(uint16 => LoanTerm) public loans; // Mapping of tokenId to borrower and term (ending block)
    uint256 public maximumDuration;

    event listingPlayerForLoan(uint16 tokenId, uint256 duration, uint256 price);
    event unlistingPlayer(uint16 tokenId);
    event loanPlayer(uint16 tokenId, address borrower, uint256 term);
    event updateMaximumDuration(uint256 duration);

    constructor(address _kickAddress, address _VRFAddress) {
        kickToken = IERC20(_kickAddress);
        verifiableRandomFootballer = IERC721(_VRFAddress);
        maximumDuration = 1300000;
    }

    function listPlayerForLoan(
        uint256 _duration, // Number of blocks
        uint256 _price, // Kick token
        uint16 _playerId
    ) external {
        if (verifiableRandomFootballer.ownerOf(_playerId) != msg.sender)
            revert NotOwner(
                msg.sender,
                verifiableRandomFootballer.ownerOf(_playerId)
            );
        if (playersForLoan[_playerId][0] > 0) revert AlreadyListed();
        if (_duration > maximumDuration)
            revert MaxDuration(_duration, maximumDuration);
        playersForLoan[_playerId][0] = _duration;
        playersForLoan[_playerId][1] = _price;
        emit listingPlayerForLoan(_playerId, _duration, _price);
    }

    function unlistPlayer(uint16 _playerId) external {
        if (verifiableRandomFootballer.ownerOf(_playerId) != msg.sender)
            revert NotOwner(
                msg.sender,
                verifiableRandomFootballer.ownerOf(_playerId)
            );
        if (playersForLoan[_playerId][0] <= 0) revert NotListed();
        playersForLoan[_playerId][0] = 0;
        playersForLoan[_playerId][1] = 0;
        emit unlistingPlayer(_playerId);
    }

    function loan(uint16 _playerId) external payable nonReentrant {
        uint256 _term = playersForLoan[_playerId][0] + block.number; // term is the block when the loans ends
        uint256 _price = playersForLoan[_playerId][1]; // price and duration of the loan are coming from the listing
        address _lender = verifiableRandomFootballer.ownerOf(_playerId);
        if (_price > kickToken.balanceOf(msg.sender))
            revert BalanceTooLow(kickToken.balanceOf(msg.sender), _price);
        if (playersForLoan[_playerId][0] <= 0) revert NotListed();
        if (block.number < loans[_playerId].term) revert AlreadyOnLoan();
        LoanTerm memory loanTerm;
        loanTerm.borrower = msg.sender;
        loanTerm.term = _term;
        loans[_playerId] = loanTerm;
        // 97.5% of the listing price goes to the owner of the player
        kickToken.transferFrom(msg.sender, _lender, (_price * 9750) / 10000);
        // 2.5% goes to this contract
        kickToken.transferFrom(
            msg.sender,
            address(this),
            (_price * 250) / 10000
        );
        emit loanPlayer(_playerId, msg.sender, _term);
    }

    function setMaximumDuration(uint256 _duration) external onlyOwner {
        maximumDuration = _duration;
        emit updateMaximumDuration(_duration);
    }

    function withdraw() external payable onlyOwner {
        kickToken.transfer(msg.sender, kickToken.balanceOf(address(this)));
    }
}
