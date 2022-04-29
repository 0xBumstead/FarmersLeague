// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/utils/Strings.sol";
import "./SvgLib.sol";

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
