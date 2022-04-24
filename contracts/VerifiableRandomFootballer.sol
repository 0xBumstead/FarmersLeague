// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "./Base64.sol";

contract VerifiableRandomFootballer is
    ERC721URIStorage,
    IERC2981,
    VRFConsumerBase,
    Ownable
{
    using Counters for Counters.Counter;
    using Strings for uint256;
    using Base64 for bytes;

    Counters.Counter private tokenIds;
    bytes32 internal keyHash;
    uint256 internal fee;
    uint256 public price; // Mint price
    mapping(bytes32 => address) internal requestIdToSender;
    mapping(bytes32 => uint16) internal requestIdToTokenId;
    mapping(uint16 => uint256) internal tokenIdToRandomNumber;

    event requestedPlayer(bytes32 requestId, uint16 tokenId);
    event PlayerWithRandomness(uint16 tokenId, uint256 randomNumber);

    error InsufficientValue(uint256 value, uint256 requested);
    error NoSupply();

    constructor(
        address _VRFCoordinator,
        address _LinkToken,
        bytes32 _keyHash,
        uint256 _fee,
        uint256 _price
    )
        VRFConsumerBase(_VRFCoordinator, _LinkToken)
        ERC721("Verifiable Random Footballer", "VRF")
    {
        fee = _fee;
        keyHash = _keyHash;
        price = _price; // ETH
        tokenIds.increment();
    }

    // Set an Id to the future NFT and request a random number to Chainlink VRF
    function requestPlayer() public payable returns (bytes32 requestId) {
        if (msg.value < price) revert InsufficientValue(msg.value, price);
        if (tokenIds.current() >= 10000) revert NoSupply();
        requestId = requestRandomness(keyHash, fee);
        requestIdToSender[requestId] = msg.sender;
        requestIdToTokenId[requestId] = uint16(tokenIds.current());
        emit requestedPlayer(requestId, uint16(tokenIds.current()));
        tokenIds.increment();
    }

    // Called by the Chainlink node following the requestRandomness function call
    // Mints the NFT (with empty token URI) and send it to its owner
    function fulfillRandomness(bytes32 _requestId, uint256 _randomNumber)
        internal
        override
    {
        address nftOwner = requestIdToSender[_requestId];
        uint16 tokenId = requestIdToTokenId[_requestId];
        _safeMint(nftOwner, tokenId);
        tokenIdToRandomNumber[tokenId] = _randomNumber;
        emit PlayerWithRandomness(tokenId, _randomNumber);
    }

    // Withdraw the ETH collected by the smart contract during the mint
    function withdraw() public payable onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }

    // EIP2981 standard royalties return : 2,5% payable to this contract
    function royaltyInfo(uint256 _tokenId, uint256 _salePrice)
        external
        view
        override
        returns (address receiver, uint256 royaltyAmount)
    {
        return (address(this), (_salePrice * 250) / 10000);
    }

    // EIP2981 standard Interface return, add to ERC1155 and ERC165 Interface returns
    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC721, IERC165)
        returns (bool)
    {
        return (interfaceId == type(IERC2981).interfaceId ||
            super.supportsInterface(interfaceId));
    }

    // Create multiple random numbers from a single VRF response
    function expand(uint256 _randomNumber, uint8 _n)
        internal
        pure
        returns (uint256[] memory expandedValues)
    {
        expandedValues = new uint256[](_n);
        for (uint256 i = 0; i < _n; i++) {
            expandedValues[i] = uint256(
                keccak256(abi.encode(_randomNumber, i))
            );
        }
        return expandedValues;
    }
}
