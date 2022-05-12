// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "./PlayerOwnership.sol";
import "../interfaces/ILeagueTeam.sol";
import "../interfaces/IGameResult.sol";

error BalanceTooLow(uint256 balance, uint256 requested);
error OnGoingGame();
error StakeTooLow(uint256 stake, uint256 requested);
error IncorrectLayout();
error TeamNotAvailable();
error TeamNotChallenged();
error TooLate(uint256 time, uint256 requested);
error TooEarly(uint256 time, uint256 requested);
error LinkBalance(uint256 balance, uint256 requested);
error AlreadySet(address contractAddress);

contract LeagueGame is
    VRFConsumerBase,
    Ownable,
    ReentrancyGuard,
    PlayerOwnership
{
    using Counters for Counters.Counter;
    IERC20 public kickToken;
    IERC20 public linkToken;
    IGameResult internal gameResult;
    ILeagueTeam internal leagueTeam;

    Counters.Counter private gameIds;
    bytes32 internal keyHash;
    uint256 internal fee;
    uint256[3] public prices; // 0 => Minimum Kick tokens to put at stake for signing up a team, 1 => price for declining challenge,
    // 2 => number of token given to the winner in addition to the stakes
    uint256 public challengeTime; // Number of blocks between the challenge and the deadline to refuse
    uint256[2] public gameDelay; // Mininum and Maximum number of blocks before setting a game time
    address public gameResultContract; // Address of the contract allowed to finish a game

    mapping(uint256 => uint256[4]) public teamGame;
    // teamId => gameId[0] (1 = team is waiting for opponent, 2 = team is challenging an opponent, 3 = team is challenged by an opponent
    // 4 = team has a game set), gameId[1] = gameId, gameId[2] = layoutId, gameId[3] = stake amount
    mapping(uint256 => uint256[3]) public games; // gameId => gameBlockNumber (0), receivingTeam (1), awayTeam (2)
    mapping(uint256 => mapping(uint256 => uint256)) public teamChallenge; // teamId => challenged teamId => deadline to refuse (number of blocks)
    mapping(bytes32 => uint256) requestIdToGameId;

    event teamSignedUp(uint256 teamId);
    event signUpCanceled(uint256 teamId);
    event teamChallenged(uint256 challengedTeamId, uint256 challengingTeamId);
    event challengeDeclined(
        uint256 challengedTeamId,
        uint256 challengingTeamId
    );
    event gameRequested(
        bytes32 requestId,
        uint256 firstTeam,
        uint256 secondTeam,
        uint256 gameId
    );
    event gameSet(uint256 gameId, uint256 blockNumber);
    event gameFinished(uint256 gameId, uint8 result);
    event updateChallengeTime(uint256 time);
    event updatePrices(
        uint256 signedUpPrice,
        uint256 declinePrice,
        uint256 winningBonus
    );
    event updateGameDelay(uint256 minTime, uint256 maxTime);

    constructor(
        address _KickToken,
        address _LeagueTeam,
        address _VerifiableRandomFootballer,
        address _PlayerLoan,
        address _VRFCoordinator,
        address _LinkToken,
        bytes32 _keyHash,
        uint256 _fee
    )
        VRFConsumerBase(_VRFCoordinator, _LinkToken)
        PlayerOwnership(_PlayerLoan, _VerifiableRandomFootballer)
    {
        kickToken = IERC20(_KickToken);
        linkToken = IERC20(_LinkToken);
        leagueTeam = ILeagueTeam(_LeagueTeam);
        fee = _fee;
        keyHash = _keyHash;
        prices = [3 * 10**18, 1 * 10**18, 2 * 10**18];
        challengeTime = 86400;
        gameDelay = [43200, 604800];
        gameIds.increment();
    }

    function signUpTeam(
        uint256 _teamId,
        uint256 _layoutId,
        uint256 _stake
    )
        external
        payable
        nonReentrant
        onlyPlayerOwner(leagueTeam.teamMembers(_teamId, 1))
    {
        if (teamGame[_teamId][0] != 0) revert OnGoingGame();
        if (kickToken.balanceOf(msg.sender) < _stake)
            revert BalanceTooLow(kickToken.balanceOf(msg.sender), _stake);
        if (_stake < prices[0]) revert StakeTooLow(_stake, prices[0]);
        if (_layoutId > 13) revert IncorrectLayout();
        teamGame[_teamId][0] = 1; // mark the team as waiting for an opponent
        teamGame[_teamId][2] = _layoutId;
        teamGame[_teamId][3] = _stake;
        kickToken.transferFrom(msg.sender, address(this), _stake); // amount staked on the game
        emit teamSignedUp(_teamId);
    }

    function cancelSignUp(uint256 _teamId)
        external
        nonReentrant
        onlyPlayerOwner(leagueTeam.teamMembers(_teamId, 1))
    {
        uint256 _stake = teamGame[_teamId][3];
        if (teamGame[_teamId][0] != 1) revert TeamNotAvailable();
        if (kickToken.balanceOf(address(this)) < _stake)
            revert BalanceTooLow(kickToken.balanceOf(address(this)), _stake);
        teamGame[_teamId] = [0, 0, 0, 0]; // mark the team as not signed up
        kickToken.transfer(msg.sender, _stake); // give back the staked token
        emit signUpCanceled(_teamId);
    }

    function challengeTeam(uint256 _teamId, uint256 _opponentTeamId)
        external
        onlyPlayerOwner(leagueTeam.teamMembers(_teamId, 1))
    {
        if (teamGame[_teamId][0] != 1 || teamGame[_opponentTeamId][0] != 1)
            revert TeamNotAvailable();
        teamGame[_teamId][0] = 2; // mark the team as challenging an opponent
        teamGame[_opponentTeamId][0] = 3; // mark the team as challenged by an opponent
        teamChallenge[_opponentTeamId][_teamId] = block.number + challengeTime; // set the deadline to refuse challenge
        emit teamChallenged(_opponentTeamId, _teamId);
    }

    function declineChallenge(uint256 _teamId, uint256 _opponentTeamId)
        external
        payable
        nonReentrant
        onlyPlayerOwner(leagueTeam.teamMembers(_teamId, 1))
    {
        if (teamGame[_teamId][0] != 3 || teamGame[_opponentTeamId][0] != 2)
            revert TeamNotChallenged();
        if (block.number > teamChallenge[_teamId][_opponentTeamId])
            revert TooLate(
                block.number,
                teamChallenge[_teamId][_opponentTeamId]
            );
        if (kickToken.balanceOf(msg.sender) < prices[1])
            revert BalanceTooLow(kickToken.balanceOf(msg.sender), prices[1]);
        teamGame[_teamId][0] = 1; // mark the team as waiting for an opponent
        teamGame[_opponentTeamId][0] = 1; // mark the opponent team as waiting for an opponent
        teamChallenge[_teamId][_opponentTeamId] = 0; // remove the pending challenge
        kickToken.transferFrom(msg.sender, address(this), prices[1]); // fee payed to the protocol to decline
        emit challengeDeclined(_teamId, _opponentTeamId);
    }

    function requestGame(uint256 _teamId, uint256 _opponentTeamId)
        external
        returns (bytes32 requestId)
    {
        if (teamGame[_teamId][0] != 2 || teamGame[_opponentTeamId][0] != 3)
            revert TeamNotAvailable();
        if (block.number < teamChallenge[_opponentTeamId][_teamId])
            revert TooEarly(
                block.number,
                teamChallenge[_opponentTeamId][_teamId]
            );
        if (linkToken.balanceOf(address(this)) < fee)
            revert LinkBalance(linkToken.balanceOf(address(this)), fee);
        uint256 _gameId = gameIds.current(); // Get a new id for the game
        gameIds.increment();
        teamGame[_teamId][0] = 4; // Mark the first team as having an on-going game
        teamGame[_opponentTeamId][0] = 4; // Mark the second team as having an on-going game
        teamGame[_teamId][1] = _gameId; // Store the gameId in first team games list
        teamGame[_opponentTeamId][1] = _gameId; // Store the gameId in second team games list
        requestId = requestRandomness(keyHash, fee); // Set the requestId that will be used to get randomness
        games[_gameId][1] = _teamId; // Set temporarily the first team as receiving team (this will get a 50% chance to be changed after fulfillRandomness)
        games[_gameId][2] = _opponentTeamId; // Set temporarily the second team as away team (this will get a 50% chance to be changed after fulfillRandomness)
        requestIdToGameId[requestId] = _gameId; // Associate the requestId with the game Id to match each random number with corresponding game
        emit gameRequested(requestId, _teamId, _opponentTeamId, _gameId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        uint256 _gameId = requestIdToGameId[_requestId]; // Get the gameId matching the requestId
        uint256 _firstTeam = games[_gameId][1]; // Get the first team
        uint256 _secondTeam = games[_gameId][2]; // Get the second team
        uint256 _gameBlockNumber = block.number +
            (_randomness % gameDelay[1]) +
            gameDelay[0];
        // Use the random number to set a game time between min and max delay
        if (_randomness % 2 == 0) {
            // Use the random number to set which team will be receiving
            // 50% chance to keep the temporary set up, 50% to chance to do the opposite
            games[_gameId][1] = _secondTeam;
            games[_gameId][2] = _firstTeam;
        }
        games[_gameId][0] = _gameBlockNumber; // Store the game block number with the gameId
        emit gameSet(_gameId, _gameBlockNumber);
    }

    function finishGame(uint256 _gameId) external nonReentrant {
        uint256 _stakes = teamGame[games[_gameId][1]][3] +
            teamGame[games[_gameId][2]][3];
        if (teamGame[games[_gameId][2]][1] != _gameId)
            revert TeamNotAvailable(); // Check the status of one team (still engaged in the game), prevents from executing the function twice
        if (kickToken.balanceOf(address(this)) < _stakes + prices[2])
            revert BalanceTooLow(
                kickToken.balanceOf(address(this)),
                _stakes + prices[2]
            );
        gameResult = IGameResult(gameResultContract);
        uint8 _result = gameResult.setResult(_gameId);
        // Transfer the stakes + bonus to owner of the captain of the winning team
        if (_result == 1) {
            kickToken.transfer(
                currentOwner(leagueTeam.teamMembers(games[_gameId][1], 1)),
                _stakes + prices[2]
            );
        } else if (_result == 2) {
            kickToken.transfer(
                currentOwner(leagueTeam.teamMembers(games[_gameId][2], 1)),
                _stakes + prices[2]
            );
        } else {
            // Split the two stakes between the two captains in case the game is a draw
            kickToken.transfer(
                currentOwner(leagueTeam.teamMembers(games[_gameId][1], 1)),
                (_stakes + prices[2]) / 2
            );
            kickToken.transfer(
                currentOwner(leagueTeam.teamMembers(games[_gameId][2], 1)),
                (_stakes + prices[2]) / 2
            );
        }
        // Clear the status of both teams
        teamGame[games[_gameId][1]] = [0, 0, 0, 0];
        teamGame[games[_gameId][2]] = [0, 0, 0, 0];
        emit gameFinished(_gameId, _result);
    }

    function setChallengeTime(uint256 _time) external onlyOwner {
        challengeTime = _time;
        emit updateChallengeTime(_time);
    }

    function setPrices(uint256[3] calldata _prices) external onlyOwner {
        prices = _prices;
        emit updatePrices(_prices[0], _prices[1], _prices[2]);
    }

    function setGameDelay(uint256[2] calldata _delays) external onlyOwner {
        gameDelay = _delays;
        emit updateGameDelay(_delays[0], _delays[1]);
    }

    function setGameResultContract(address _gameResult) external onlyOwner {
        if (gameResultContract != address(0x0))
            revert AlreadySet(gameResultContract);
        gameResultContract = _gameResult;
    }

    function withdrawLink() external payable onlyOwner {
        linkToken.transfer(msg.sender, linkToken.balanceOf(address(this)));
    }

    function withdraw() external payable onlyOwner {
        kickToken.transfer(msg.sender, kickToken.balanceOf(address(this)));
    }
}
