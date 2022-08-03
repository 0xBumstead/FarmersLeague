// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

error NotOwner(address sender, address owner);
error AlreadyListed();
error NotListed();
error NotApproved();
error BalanceTooLow(uint256 balance, uint256 requested);

contract PlayerTransfer is Ownable, ReentrancyGuard {
    IERC20 public kickToken;
    IERC721 public verifiableRandomFootballer;

    mapping(uint16 => uint256) public playersForTransfer; // Mapping of tokenId to price
    uint16[] internal transferList;

    event listingPlayerForTransfer(uint16 tokenId, uint256 price);
    event unlistingPlayer(uint16 tokenId);

    constructor(address _kickAddress, address _VRFAddress) {
        kickToken = IERC20(_kickAddress);
        verifiableRandomFootballer = IERC721(_VRFAddress);
    }

    function listPlayerForTransfer(uint256 _price, uint16 _playerId) external {
        if (verifiableRandomFootballer.ownerOf(_playerId) != msg.sender)
            revert NotOwner(
                msg.sender,
                verifiableRandomFootballer.ownerOf(_playerId)
            );
        if (playersForTransfer[_playerId] > 0) revert AlreadyListed();
        if (verifiableRandomFootballer.getApproved(_playerId) != address(this))
            revert NotApproved();
        playersForTransfer[_playerId] = _price;
        uint256 _listLength = transferList.length;
        for (uint256 i = 0; i < _listLength; ++i) {
            if (transferList[i] == 0) {
                transferList[i] = _playerId;
                break;
            } else if (i == transferList.length - 1) {
                transferList.push(_playerId);
            }
        }
        if (transferList.length == 0) {
            transferList.push(_playerId);
        }
        emit listingPlayerForTransfer(_playerId, _price);
    }

    function unlistPlayer(uint16 _playerId) external {
        if (verifiableRandomFootballer.ownerOf(_playerId) != msg.sender)
            revert NotOwner(
                msg.sender,
                verifiableRandomFootballer.ownerOf(_playerId)
            );
        if (playersForTransfer[_playerId] <= 0) revert NotListed();
        playersForTransfer[_playerId] = 0;
        for (uint256 i = 0; i < transferList.length; ++i) {
            if (transferList[i] == _playerId) {
                transferList[i] = 0;
                break;
            }
        }
        emit unlistingPlayer(_playerId);
    }

    function transfer(uint16 _playerId) external payable nonReentrant {
        uint256 _price = playersForTransfer[_playerId]; // price of the transfer is coming from the listing
        address _seller = verifiableRandomFootballer.ownerOf(_playerId);
        if (_price > kickToken.balanceOf(msg.sender))
            revert BalanceTooLow(kickToken.balanceOf(msg.sender), _price);
        if (playersForTransfer[_playerId] <= 0) revert NotListed();
        // 97.5% of the listing price goes to the owner of the player
        kickToken.transferFrom(msg.sender, _seller, (_price * 9750) / 10000);
        // 2.5% goes to this contract
        kickToken.transferFrom(
            msg.sender,
            address(this),
            (_price * 250) / 10000
        );
        verifiableRandomFootballer.safeTransferFrom(
            _seller,
            msg.sender,
            _playerId
        );
        playersForTransfer[_playerId] = 0; //remove the player from the transfer list
        for (uint256 i = 0; i < transferList.length; ++i) {
            if (transferList[i] == _playerId) {
                transferList[i] = 0;
                break;
            }
        }
        emit unlistingPlayer(_playerId);
    }

    function getTransferListArray()
        external
        view
        returns (uint16[] memory transfertListArray)
    {
        return transferList;
    }

    function withdraw() external payable onlyOwner {
        kickToken.transfer(msg.sender, kickToken.balanceOf(address(this)));
    }
}
