// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library UnsafeMath8 {
    function unsafe_add(uint8 a, uint8 b) internal pure returns (uint8) {
        unchecked {
            return a + b;
        }
    }

    function unsafe_sub(uint8 a, uint8 b) internal pure returns (uint8) {
        unchecked {
            return a - b;
        }
    }

    function unsafe_div(uint8 a, uint8 b) internal pure returns (uint8) {
        unchecked {
            uint8 result;
            assembly {
                result := div(a, b)
            }
            return result;
        }
    }

    function unsafe_mul(uint8 a, uint8 b) internal pure returns (uint8) {
        unchecked {
            return a * b;
        }
    }

    function unsafe_increment(uint8 a) internal pure returns (uint8) {
        unchecked {
            return ++a;
        }
    }

    function unsafe_decrement(uint8 a) internal pure returns (uint8) {
        unchecked {
            return --a;
        }
    }
}

library UnsafeMath256 {
    function unsafe_add(uint256 a, uint256 b) internal pure returns (uint256) {
        unchecked {
            return a + b;
        }
    }

    function unsafe_sub(uint256 a, uint256 b) internal pure returns (uint256) {
        unchecked {
            return a - b;
        }
    }

    function unsafe_div(uint256 a, uint256 b) internal pure returns (uint256) {
        unchecked {
            uint8 result;
            assembly {
                result := div(a, b)
            }
            return result;
        }
    }

    function unsafe_mul(uint256 a, uint256 b) internal pure returns (uint256) {
        unchecked {
            return a * b;
        }
    }

    function unsafe_increment(uint256 a) internal pure returns (uint256) {
        unchecked {
            return ++a;
        }
    }

    function unsafe_decrement(uint256 a) internal pure returns (uint256) {
        unchecked {
            return --a;
        }
    }
}
