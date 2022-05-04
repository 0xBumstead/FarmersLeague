// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./PlayerOwnership.sol";

error OnLoan();
error AlreadyInTeam(uint256 teamId);
error BalanceTooLow(uint256 balance, uint256 requested);
error AlreadyApplied();
error TeamFull();
error CaptainId();
error NotInTeam();

contract LeagueTeam is Ownable, ReentrancyGuard, PlayerOwnership {
    using Counters for Counters.Counter;
    IERC20 public kickToken;

    Counters.Counter private teamIds; // Count the number of existing teams
    uint256 public teamCreationPrice;
    uint256 public releasePrice;
    mapping(uint16 => uint256) public playersTeam; // Identify the team in which the player is enrolled
    mapping(uint256 => uint16[24]) public teamMembers; // Identify the players enrolled in a team - first position stores the number of team members
    mapping(uint16 => uint256) public playersApplication; // Identify the team for which the player has applied
    mapping(uint256 => uint16[]) public teamApplications; // list the players that applied for a team and are waiting for an approval - first position stores the number of application

    event updateTeamCreationPrice(uint256 price);
    event updateReleasePrice(uint256 price);
    event teamCreation(uint256 teamId, uint16 captainId);
    event teamRemoval(uint256 teamId);
    event playerApplication(uint16 playerId, uint256 teamId);
    event applicationCanceled(uint16 playerId, uint256 teamId);
    event applicationValidated(
        uint16 playerId,
        uint256 teamId,
        uint256 position
    );
    event applicationsCleared(uint256 teamId);
    event playerReleased(uint16 playerId, uint256 teamId);

    constructor(
        address _KickToken,
        address _VerifiableRandomFootballer,
        address _PlayerLoan,
        uint256 _teamCreationPrice,
        uint256 _releasePrice
    ) PlayerOwnership(_PlayerLoan, _VerifiableRandomFootballer) {
        kickToken = IERC20(_KickToken);
        teamIds.increment();
        teamCreationPrice = _teamCreationPrice;
        releasePrice = _releasePrice;
    }

    function createTeam(uint16 _captainId) external payable nonReentrant {
        (, uint256 _term) = playerLoan.loans(_captainId);
        if (verifiableRandomFootballer.ownerOf(_captainId) != msg.sender)
            revert NotOwner(
                msg.sender,
                verifiableRandomFootballer.ownerOf(_captainId)
            ); // Only its true owner can use a player to create a team, this cannot be done through loan ownership
        if (_term > block.number) revert OnLoan();
        if (playersTeam[_captainId] > 0)
            revert AlreadyInTeam(playersTeam[_captainId]);
        if (kickToken.balanceOf(msg.sender) < teamCreationPrice)
            revert BalanceTooLow(
                kickToken.balanceOf(msg.sender),
                teamCreationPrice
            );
        teamMembers[teamIds.current()][0] = 1; // team is now 1 player size
        teamMembers[teamIds.current()][1] = _captainId; // member[1] of a new team is its captain
        playersTeam[_captainId] = teamIds.current(); // mark the player as part a team
        teamApplications[teamIds.current()].push(0); // Initialize the number of applications
        kickToken.transferFrom(msg.sender, address(this), teamCreationPrice); // fee payed to the protocol to create a team
        emit teamCreation(teamIds.current(), _captainId);
        teamIds.increment();
    }

    function removeTeam(uint256 _teamId) external {
        uint16 _captainId = teamMembers[_teamId][1];
        (, uint256 _term) = playerLoan.loans(_captainId);
        if (verifiableRandomFootballer.ownerOf(_captainId) != msg.sender)
            revert NotOwner(
                msg.sender,
                verifiableRandomFootballer.ownerOf(_captainId)
            ); // Only its true owner can use a player to delete a team, this cannot be done through loan ownership
        if (_term > block.number) revert OnLoan();
        for (uint8 i = 0; i < 23; ++i) {
            // Loop through all the players of the team and erase them from the team
            playersTeam[teamMembers[_teamId][i]] = 0;
            teamMembers[_teamId][i] = 0;
        }
        emit teamRemoval(_teamId);
    }

    function applyForTeam(uint16 _playerId, uint256 _teamId)
        external
        onlyPlayerOwner(_playerId)
    {
        if (playersApplication[_playerId] > 0) revert AlreadyApplied();
        if (playersTeam[_playerId] > 0)
            revert AlreadyInTeam(playersTeam[_playerId]);
        if (teamMembers[_teamId][0] >= 23) revert TeamFull();
        teamApplications[_teamId].push(_playerId); // player applies to the first available position
        teamApplications[_teamId][0] = teamApplications[_teamId][0] + 1; // stores the number of applications for this team
        playersApplication[_playerId] = _teamId; // mark the player as having an ongoing application
        emit playerApplication(_playerId, _teamId);
    }

    function cancelApplication(uint16 _playerId, uint256 _teamId)
        external
        onlyPlayerOwner(_playerId)
    {
        uint16 _applicationsNumber = teamApplications[_teamId][0];
        for (uint16 i = 1; i <= _applicationsNumber; ++i) {
            // Loop through the applications to find the player
            if (teamApplications[_teamId][i] == _playerId) {
                teamApplications[_teamId][i] = 0; // remove the application
                playersApplication[_playerId] = 0; // clear the player application
                break;
            }
        }
        emit applicationCanceled(_playerId, _teamId);
    }

    function validateApplication(uint16 _playerId, uint256 _teamId)
        external
        onlyPlayerOwner(teamMembers[_teamId][1])
    {
        uint8 _playersNumber = uint8(teamMembers[_teamId][0]);
        if (_playersNumber >= 23) revert TeamFull();
        uint16 _applicationsNumber = teamApplications[_teamId][0];
        for (uint16 i = 1; i <= _applicationsNumber; ++i) {
            // Loop through the applications to find the player
            if (teamApplications[_teamId][i] == _playerId) {
                teamApplications[_teamId][i] = 0; // remove application
                for (uint8 j = 2; j <= _playersNumber + 1; j++) {
                    // Loop through the team members to find an empty position
                    if (teamMembers[_teamId][j] == 0) {
                        teamMembers[_teamId][j] = _playerId; // enroll player
                        teamMembers[_teamId][0] = _playersNumber + 1; // increase number of team members
                        playersTeam[_playerId] = _teamId; // mark the player as a team member
                        playersApplication[_playerId] = 0; // clear the player application
                        emit applicationValidated(_playerId, _teamId, j);
                        break;
                    }
                }
                break;
            }
        }
    }

    function clearApplications(uint256 _teamId)
        external
        onlyPlayerOwner(teamMembers[_teamId][1])
    {
        uint16 _applicationsNumber = teamApplications[_teamId][0];
        for (uint16 i = 1; i <= _applicationsNumber; ++i) {
            uint16 _playerId = teamApplications[_teamId][i];
            if (_playerId != 0) {
                playersApplication[_playerId] = 0; // clear the player application
                teamApplications[_teamId][i] = 0; // remove all players id from applications
            }
        }
        emit applicationsCleared(_teamId);
    }

    function releasePlayer(uint16 _playerId, uint256 _teamId)
        external
        onlyPlayerOwner(teamMembers[_teamId][1])
    {
        if (_playerId == teamMembers[_teamId][1]) revert CaptainId();
        if (playersTeam[_playerId] != _teamId) revert NotInTeam();
        removePlayer(_playerId, _teamId); // the removePlayer function can be called through the captain way or the pay clause way
    }

    function removePlayer(uint16 _playerId, uint256 _teamId) internal {
        uint16 _playersNumber = teamMembers[_teamId][0];
        for (uint16 i = 2; i <= _playersNumber; ++i) {
            // Loop through the team members to find the player
            if (teamMembers[_teamId][i] == _playerId) {
                teamMembers[_teamId][i] = 0; // remove the player from the team
                teamMembers[_teamId][0] = _playersNumber - 1; // decrease the players number of the team
                playersTeam[_playerId] = 0; // unmark the player as team member
                emit playerReleased(_playerId, _teamId);
                break;
            }
        }
    }

    function payReleaseClause(uint16 _playerId)
        external
        payable
        nonReentrant
        onlyPlayerOwner(_playerId)
    {
        if (kickToken.balanceOf(msg.sender) < releasePrice)
            revert BalanceTooLow(kickToken.balanceOf(msg.sender), releasePrice);
        uint256 _teamId = playersTeam[_playerId];
        address _owner = verifiableRandomFootballer.ownerOf(
            teamMembers[_teamId][1]
        );
        kickToken.transferFrom(
            msg.sender,
            address(this),
            ((releasePrice * 250) / 10000)
        ); // 2.5% royalties for this contract
        kickToken.transferFrom(
            msg.sender,
            _owner,
            ((releasePrice * 9750) / 10000)
        ); // 97,5% of the price to the owner of the team
        removePlayer(_playerId, _teamId);
    }

    function withdraw() external payable onlyOwner {
        kickToken.transfer(msg.sender, kickToken.balanceOf(address(this)));
    }

    function setTeamCreationPrice(uint256 _price) external onlyOwner {
        teamCreationPrice = _price;
        emit updateTeamCreationPrice(_price);
    }

    function setReleasePrice(uint256 _price) external onlyOwner {
        releasePrice = _price;
        emit updateReleasePrice(_price);
    }
}
