// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "./Base64.sol";

library SvgLib {
    struct Image {
        string[3] backgroundColor;
        string[3] shoesColor;
        string[2] skinColor;
        string[2] skinShadow;
        string[4] hairColor;
        string[7] haircut;
        string[10] beard;
        string[3] rightHand;
        string[2] rightLeg;
        string[10] outfit;
    }

    function generatesSvg(uint8[15] calldata _scores)
        external
        pure
        returns (string memory)
    {
        Image memory image;

        image.backgroundColor = ["#9eb89e", "#ff9200", "#baffc9"];
        image.shoesColor = ["#000000", "#fdfbfb", "#eac117"];
        image.skinColor = ["#f1c27d", "#6f4f1d"];
        image.skinShadow = ["#d9a066", "#4d3714"];
        image.hairColor = ["#75250a", "#fde968", "#905424", "#14100b"];
        image.haircut = [
            '<path class="hair" d="M16 10h1v-4h1v-1h7v1h1v4h1v-6h-1v-1h-1v-1h-7v1h-1v1h-1M18 8h2v1h-2M23 8h2v1h-2" />',
            '<path class="hair" d="M15 11h1v-1h1v-2h1v-2h1v-1h1v1h1v-1h1v1h1v-1h1v1h1v2h1v2h1v1h1v-2h-1v-4h-1v-2h-1v-1h-7v1h-1v2h-1v3h-1M16 12h1v2h1v1h1v1h-1v1h-1v-1h-2v-1h1v-1h-1v-1h1M26 12h1v1h1v1h-1v1h1v1h-2v1h-1v-1h-1v-1h1v-1h1 M18 8h2v1h-2M23 8h2v1h-2" />',
            '<path class="hair" d="M15 10h1v1h1v3h1v6h-1v-1h-1v-4h-1M15 10h2v-1h1v-2h1v-1h1v-1h2v-3h-3v1h-1v1h-1v1h-1v3h-1M22 2h2v1h2v1h1v2h1v8h-1v7h-1v-1h-1v-7h1v-4h-1v-2h-1v-1h-2 M18 9h2v1h-2M23 9h2v1h-2" />',
            '<path class="hair" d="M16 10h1v-3h-1M17 7h1v-2h-1M18 5h2v-1h-2M20 4h3v-1h-3M23 5h2v-1h-2M25 5h1v2h-1M26 7h1v3h-1M18 8h2v1h-2M23 8h2v1h-2" />',
            '<path class="hair" d="M16 10h1v-3h1v-1h1v-1h5v1h1v1h1v3h1v-6h-1v-1h-10 M18 8h2v1h-2M23 8h2v1h-2" />',
            '<path class="hair" d="M16 10h1v-3h1v-1h2v-1h3v-1h1v-1h1v-1h-1v-1h-5v1h-1v1h-1v1h-1M26 10h1v-6h-1v-1h-1v1h-1v2h1v1h1 M18 8h2v1h-2M23 8h2v1h-2"/><path class="skin" d="M24 3h1v1h-1"/>',
            '<path class="hair" d="M16 10h1v-3h1v-2h1v-1h1v1h3v-4h-4v1h-1v1h-1v1h-1 M26 10h1v-6h-1v-1h-1v-1h-1v-1h-1v3h1v1h1v2h1 M18 8h2v1h-2M23 8h2v1h-2"/>'
        ];
        image.beard = [
            "",
            "",
            "",
            "",
            "",
            '<path class="hair" d="M17 12h1v1h1v1h1v-1h3v1h1v-1h1v-1h1v2h-1v2h-1v1h-5v-1h-1v-2h-1" />',
            '<path class="hair" d="M17 12h1v1h1v1h1v-1h3v1h1v-1h1v-1h1v2h-1v2h-1v1h-5v-1h-1v-2h-1" />',
            '<path class="hair" d="M20 13h3v1h-3M19 14h1v2h1v-1h1v1h1v-2h1v3h-1v1h-3v-1h-1" />',
            '<path class="hair" d="M20 13h3v1h-3M19 14h1v2h1v-1h1v1h1v-2h1v3h-1v1h-3v-1h-1" />',
            '<path class="hair" d="M19 15h5v-2h-5" />'
        ];
        image.rightHand = [
            '<path class="skin" d="M12 23h1v1h-1" />',
            '<path class="skin" d="M10 24h1v1h-1" />',
            '<path class="skin" d="M12 23h1v1h-1" /><path class="skin" d="M10 24h1v1h-1" />'
        ];
        image.rightLeg = [
            '<path class="skin" d="M18 32h2v2h-2" /><path class="socks" d="M18 33h2v4h-2" /><path class="socks-side" d="M18 33h2v1h-2" /><path class="shoes" d="M20 37h-3v1h-1v1h4" /><path class="shadow" d="M20 37h2v1h5v1h-3v1h-4" /><path class="black" d="M20 39h-4v1h4" />',
            '<g class="move-right"><path class="skin" d="M16 29h2v1h-2" /><path class="socks" d="M16 30h2v3h-2" /><path class="socks-side" d="M16 30h2v1h-2" /><path class="shoes" d="M15 33h3v2h-4v-1h1" /><path class="ball" d="M14 35h4v4h-4" /><path class="black" d="M14 35h1v1h-1M15 36h1v1h-1M16 37h1v1h-1M17 38h1v1h-1M16 35h2v1h-2M13 36h1v2h-1M18 36h1v2h-1M15 39h2v1h-2M14 38h1v1h-1" /><path class="shadow" d="M17 39h3v1h-3" /></g>'
        ];

        image.outfit = [
            ".socks { fill: #a00000 } .socks-side { fill: #000000 } .shorts { fill: #000000 } .shirt { fill: #a00000 } .shirt-side { fill: #000000 } .stripes { fill: #000000 }",
            ".socks { fill: #011f4b } .socks-side { fill: #000000 } .shorts { fill: #000000 } .shirt { fill: #011f4b } .shirt-side { fill: #000000 } .stripes { fill: #000000 }",
            ".socks { fill: #fdfbfb } .socks-side { fill: #000000 } .shorts { fill: #000000 } .shirt { fill: #000000 } .shirt-side { fill: #000000 } .stripes { fill: #fdfbfb }",
            ".socks { fill: #011f4b } .socks-side { fill: #740001 } .shorts { fill: #740001 } .shirt { fill: #011f4b } .shirt-side { fill: #011f4b } .stripes { fill: #740001 }",
            ".socks { fill: #71c7ec } .socks-side { fill: #fdfbfb } .shorts { fill: #71c7ec } .shirt { fill: #71c7ec } .shirt-side { fill: #fdfbfb } .stripes { fill: #71c7ec }",
            ".socks { fill: #a00000 } .socks-side { fill: #fdfbfb } .shorts { fill: #a00000 } .shirt { fill: #a00000 } .shirt-side { fill: #fdfbfb } .stripes { fill: #a00000 }",
            ".socks { fill: #090088 } .socks-side { fill: #fdfbfb } .shorts { fill: #090088 } .shirt { fill: #090088 } .shirt-side { fill: #fdfbfb } .stripes { fill: #090088 }",
            ".socks { fill: #fdfbfb } .socks-side { fill: #71c7ec } .shorts { fill: #fdfbfb } .shirt { fill: #fdfbfb } .shirt-side { fill: #71c7ec } .stripes { fill: #fdfbfb }",
            ".socks { fill: #fdfbfb } .socks-side { fill: #6abe30 } .shorts { fill: #0000ff } .shirt { fill: #fbf236 } .shirt-side { fill: #6abe30 } .stripes { fill: #fbf236 }",
            ".socks { fill: #cf142b } .socks-side { fill: #000000 } .shorts { fill: #fdfbfb } .shirt { fill: #0300f3 } .shirt-side { fill: #000000 } .stripes { fill: #0300f3 }"
        ];

        return
            string.concat(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 42 42">',
                "<style>",
                ".background { fill: ",
                image.backgroundColor[_scores[6]],
                " }",
                ".shoes { fill: ",
                image.shoesColor[_scores[7]],
                " }",
                ".skin { fill: ",
                image.skinColor[_scores[8]],
                " }",
                ".skin-shadow { fill: ",
                image.skinShadow[_scores[8]],
                " }",
                ".hair { fill: ",
                image.hairColor[_scores[9]],
                " }",
                image.outfit[_scores[12]],
                ".black { fill: #000000 }",
                ".white { fill: #ffffff }",
                ".shadow { fill: #4c5029 }",
                ".ball { fill: #cbdbfc }",
                ".move-right { animation: 1s move-right infinite alternate ease-in-out; }",
                "@keyframes move-right { from { transform: translateY(0px); } to { transform: translateX(1px) ; } }  ",
                "</style>",
                '<rect class="background" width="100%" height="100%" />',
                '<path class="shirt" d="M17 18h9v9h-9" />',
                '<path class="stripes" d="M17 18h1v9h-1M19 18h1v9h-1M21 18h1v9h-1M23 18h1v9h-1M25 18h1v9h-1" />',
                '<path class="shirt-side" d="M18 17h7v1h-7M20 18h3v1h-3M21 19h1v1h-1" />',
                '<path class="shirt" d="M15 19h2v3h-2" />',
                '<path class="shirt-side" d="M15 19h1v1h-1M16 18h2v1h-2" />',
                '<path class="skin" d="M15 22h2v4h-6v-2h4" />',
                image.rightHand[_scores[11]],
                '<path class="shirt" d="M26 19h2v3h-2" />',
                '<path class="shirt-side" d="M25 18h2v1h-2M27 19h1v3h-1" />',
                '<path class="skin" d="M26 22h2v7h-1v1h-1" />',
                '<path class="shorts" d="M17 27h9v5h-4v-2h-1v2h-4" />',
                '<path class="skin" d="M17 5h9v9h-9M18 14h7v2h-7M19 16h5v1h-5M19 5h5v-1h-5" />',
                '<path class="skin-shadow" d="M16 10h1v2h-1M22 9h1v4h-3v-1h2M26 10h1v2h-1v2h-1v-3h1M24 15h1v1h-1M23 16h1v1h-1M20 17h3v1h-3" />',
                image.beard[_scores[14]],
                '<path class="white" d="M18 10h2v1h-2M23 10h2v1h-2M20 14h3v1h-3" />',
                '<path class="black" d="M18 10 h1v1h-1M23 10h1v1h-1" />',
                image.haircut[_scores[13]],
                image.rightLeg[_scores[10]],
                '<path class="skin" d="M23 32h2v2h-2" />',
                '<path class="socks" d="M23 33h2v4h-2" />',
                '<path class="socks-side" d="M23 33h2v1h-2" />',
                '<path class="shoes" d="M23 37h3v1h1v1h-4" />',
                '<path class="shadow" d="M26 37h2v1h5v1h-3v1h-3v-2h-1" />',
                '<path class="black" d="M23 39h4v1h-4" />',
                "</svg>"
            );
    }
}

library MetadataLib {
    using Strings for uint256;
    using SvgLib for string;

    struct Metadata {
        string strAttributes; // Attributes as string used in the token URI
        string svg;
        uint8[6] uintAttributes; // Attributes as uint to be stored in the VerifiableRandomFootballer contract, and retrieved by the PlayerRate contract
    }

    function generatesMetadata(
        Metadata memory metadata,
        uint256[] calldata _randomValues
    ) external pure returns (Metadata memory) {
        // Attributes
        uint8[15] memory scores; // Random numbers derived from random values through modulo (%)
        uint8[2] memory ratings; // 0 --> Defensive rating, 1 --> Attacking rating
        string[11] memory positionLine11; // Used for preferred position. Player position on the field is split between line and side
        string[11] memory positionSide11;
        string[4] memory positionLine4; // Used for compatible positions
        string[3] memory positionSide3;
        string[3] memory strPositions;
        uint8[6] memory _uintAttributes;

        // To match good distribution of preferred positions, we use 11 values (GK + 4-4-2)
        positionLine11 = [
            "D",
            "D",
            "D",
            "D",
            "DM",
            "DM",
            "AM",
            "AM",
            "F",
            "F",
            "GK"
        ];
        // Side repartition is asymetric with more players ables to play on the right side of the field
        positionSide11 = ["C", "C", "C", "C", "C", "R", "R", "R", "L", "L", ""];
        // For compatible positions attributes, we use straight distribution
        positionLine4 = ["D", "DM", "AM", "F"];
        positionSide3 = ["C", "R", "L"];

        scores[0] = uint8(_randomValues[0] % 11); // positionLine
        if (scores[0] < 10) {
            scores[1] = uint8(_randomValues[1] % 10); // positionSide
            scores[2] = uint8(_randomValues[2] % 4); // number of compatibles positions
        } else {
            scores[1] = 10; // no side for GK
            scores[2] = 0; // no compatible positions for GK
        }

        // Preferred position is a single attribute made from a line and a side
        strPositions[0] = string(
            abi.encodePacked(
                positionLine11[scores[0]],
                positionSide11[scores[1]]
            )
        );

        // Preferred positions is stored as uint, see PlayerRate contract for correspondence
        _uintAttributes[0] = scores[0] * 10 + scores[1];

        // Compatibles positions (loop through the number of compatible positions)
        for (uint8 i = 0; i < scores[2]; ++i) {
            // Compatible position is made from a line and a side
            uint256 _positionLine = uint256(
                keccak256(abi.encode(_randomValues[3], i))
            ) % 4;
            uint256 _positionSide = uint256(
                keccak256(abi.encode(_randomValues[3], i))
            ) % 3;
            // Compatible positions are stored as uint, see PlayerRate contract for correspondence
            _uintAttributes[i + 1] =
                uint8(_positionLine) *
                10 +
                uint8(_positionSide);
            strPositions[1] = string.concat(
                positionLine4[_positionLine],
                positionSide3[_positionSide]
            );

            if (
                keccak256(abi.encodePacked(strPositions[0])) !=
                keccak256(abi.encodePacked(strPositions[1]))
            ) {
                // All compatibles positions are grouped on a single attribute
                strPositions[2] = string.concat(
                    strPositions[2],
                    strPositions[1],
                    ", "
                );
            }
        }

        // Position correction to consider GK as most defensive player
        if (scores[0] == 10) {
            scores[0] = 0;
        } else {
            scores[0]++;
        }

        scores[4] = uint8(_randomValues[4] % 100) + 1; // Used for defense rating
        scores[5] = uint8(_randomValues[5] % 100) + 1; // Used for attack rating

        // The more defensive preferred position a player has, the higher his chances to get a good defense rating
        // scores[0] is preferred position line, out of 11, low numbers for defense, high numbers for attack
        if (scores[4] > (scores[0] * 10) / 3) {
            ratings[0] = (scores[4] - (scores[0] * 10) / 3) / 10;
        } else {
            ratings[0] = 0;
        }
        // The more defensive preferred position a player has, the lower his chances to get a good attack rating
        if (scores[5] > (100 - scores[0] * 10) / 3) {
            ratings[1] = (scores[5] - (100 - scores[0] * 10) / 3) / 10;
        } else {
            ratings[1] = 0;
        }

        metadata.strAttributes = string.concat(
            '{"trait_type": "Preferred position", "value": "',
            strPositions[0],
            '"}, ',
            '{"trait_type": "Compatible positions", "value": "',
            strPositions[2],
            '"}, ',
            '{"trait_type": "Defense", "value": ',
            uint256(ratings[0]).toString(),
            "}, ",
            '{"trait_type": "Attack", "value": ',
            uint256(ratings[1]).toString(),
            "}"
        );

        // backgroundColor, only good defensive players can get a chance to have a special background color
        if (ratings[0] >= 8) {
            scores[6] = uint8(_randomValues[6] % 3);
        } else {
            scores[6] = 0;
        }
        // shoesColor, only good attacking players can get a chance to have a special shoes color
        if (ratings[1] >= 8) {
            scores[7] = uint8(_randomValues[7] % 3);
        } else {
            scores[7] = 0;
        }
        // skinColor, Black or white, 50% chance for each
        scores[8] = uint8(_randomValues[8] % 2);
        // hairColor, Blond, brown, red, black 25% each
        scores[9] = uint8(_randomValues[9] % 4);
        // rightLeg (0 = fixed, 1 = moving with ball)
        // Only very good defensive and attacking players can get a chance to have a moving right leg
        scores[10] = uint8(_randomValues[10] % 4);
        if (scores[10] == 3 && ratings[0] + ratings[1] > 10) {
            scores[10] = 1;
        } else {
            scores[10] = 0;
        }
        // right hand (0 = thumb, 1 = index, 2 = both)
        scores[11] = uint8(_randomValues[11] % 3);
        // outfit colors
        scores[12] = uint8(_randomValues[12] % 10);
        // haircut
        scores[13] = uint8(_randomValues[13] % 7);
        // beard
        scores[14] = uint8(_randomValues[14] % 10);

        metadata.svg = SvgLib.generatesSvg(scores);

        _uintAttributes[4] = ratings[0];
        _uintAttributes[5] = ratings[1];
        metadata.uintAttributes = _uintAttributes;

        return metadata;
    }
}

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
