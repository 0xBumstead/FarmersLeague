// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "./Base64.sol";
import "./MetadataLib.sol";

contract VerifiableRandomFootballer is
    ERC721URIStorage,
    IERC2981,
    VRFConsumerBase,
    Ownable
{
    using Counters for Counters.Counter;
    using Strings for uint256;
    using Base64 for bytes;
    using MetadataLib for MetadataLib.Metadata; // Library that calculates attributes and svg from 13 random values (one random number expanded into 13)

    Counters.Counter private tokenIds;
    bytes32 internal keyHash;
    uint256 internal fee;
    uint256 public price; // Mint price
    mapping(bytes32 => address) internal requestIdToSender;
    mapping(bytes32 => uint16) internal requestIdToTokenId;
    mapping(uint16 => uint256) internal tokenIdToRandomNumber;
    mapping(uint16 => uint8[6]) public tokenIdToAttributes; // Used by the PlayerRate contract

    event requestedPlayer(bytes32 requestId, uint16 tokenId);
    event PlayerWithRandomness(uint16 tokenId, uint256 randomNumber);
    event PlayerGenerated(uint16 tokenId, string tokenURI);

    error InsufficientValue(uint256 value, uint256 requested);
    error NoSupply();
    error TokenURISet();
    error TokenNotMinted();
    error VRFnotReady();
    error NotOwner(address sender, address owner);

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
    function requestPlayer() external payable returns (bytes32 requestId) {
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

    // Creates the metadata for the newly minted empty NFT
    // using the setTokenURI function and the random number provided by Chainlink node
    function generatePlayer(uint16 _tokenId) external {
        if (bytes(tokenURI(_tokenId)).length > 0) revert TokenURISet();
        if (_tokenId > tokenIds.current()) revert TokenNotMinted();
        if (tokenIdToRandomNumber[_tokenId] == 0) revert VRFnotReady();
        if (ownerOf(_tokenId) != msg.sender)
            revert NotOwner(msg.sender, ownerOf(_tokenId));
        uint256 randomNumber = tokenIdToRandomNumber[_tokenId];
        uint256[] memory randomValues = expand(randomNumber, 15);
        MetadataLib.Metadata memory metadata;
        metadata = metadata.generatesMetadata(randomValues);
        _setTokenURI(
            _tokenId,
            formatTokenURI(_tokenId, metadata.strAttributes, metadata.svg)
        );
        tokenIdToAttributes[_tokenId] = metadata.uintAttributes;
        emit PlayerGenerated(_tokenId, metadata.svg);
    }

    // Withdraw the ETH collected by the smart contract during the mint
    function withdraw() external payable onlyOwner returns (bool success) {
        uint256 amount = address(this).balance;
        (success, ) = payable(owner()).call{value: amount}("");
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

    // Encode all the metadata (attribute and image svg) into a single token URI
    function formatTokenURI(
        uint16 _tokenId,
        string memory _attributes,
        string memory _svg
    ) internal pure returns (string memory) {
        return
            string.concat(
                "data:application/json;base64,",
                Base64.encode(
                    bytes(
                        string.concat(
                            '{"name": "Football player #',
                            uint256(_tokenId).toString(),
                            '",',
                            '"description": "Verified Random Footballer from Farmers league",',
                            '"attributes": [',
                            _attributes,
                            "],",
                            '"image": "data:image/svg+xml;base64,',
                            Base64.encode(bytes(_svg)),
                            '"}'
                        )
                    )
                )
            );
    }

    // Create multiple random numbers from a single VRF response
    function expand(uint256 _randomNumber, uint8 _n)
        internal
        pure
        returns (uint256[] memory expandedValues)
    {
        expandedValues = new uint256[](_n);
        for (uint256 i = 0; i < _n; ++i) {
            expandedValues[i] = uint256(
                keccak256(abi.encode(_randomNumber, i))
            );
        }
        return expandedValues;
    }
}
