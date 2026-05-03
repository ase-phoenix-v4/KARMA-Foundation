// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title KARMA NETWORK — Core Contract v2.0
 * @dev Tokenomics: Architect 30%, Igor 1%, Team 5%, Investors 20%, Public 20%, DAO 24%
 *      Burn 10%, LP 5%, Bonding Curve, Anti-Whale, Multisig, Staking 25% APY
 */

contract KARMANetwork {
    string public constant name = "KARMA Network";
    string public constant symbol = "KARMA";
    uint8 public constant decimals = 18;
    uint256 public constant TOTAL_SUPPLY = 1_000_000_000 * 10**18;

    uint256 public constant ARCHITECT_SHARE = 300_000_000 * 10**18;
    uint256 public constant IGOR_SHARE = 10_000_000 * 10**18;
    uint256 public constant TEAM_SHARE = 50_000_000 * 10**18;
    uint256 public constant INVESTOR_SHARE = 200_000_000 * 10**18;
    uint256 public constant PUBLIC_SHARE = 200_000_000 * 10**18;
    uint256 public constant DAO_SHARE = 240_000_000 * 10**18;

    address public immutable ARCHITECT;
    address public IGOR;
    address public constant BURN_ADDRESS = address(0xdead);
    address public TEAM_WALLET;
    address public INVESTOR_WALLET;
    address public DAO_WALLET;
    address public LIQUIDITY_POOL;

    address[] public owners;
    mapping(address => bool) public isOwner;
    uint256 public immutable VESTING_START;
    uint256 public architectUnlocked;
    uint256 public constant BASE_PRICE = 0.0001 ether;
    uint256 public constant CURVE_SLOPE = 0.00000001 ether;
    uint256 public constant MAX_HOLD = TOTAL_SUPPLY / 100;
    uint256 public constant MAX_SELL_PER_HOUR = TOTAL_SUPPLY / 200;
    uint256 public burnRate = 10;
    uint256 public lpRate = 5;
    uint256 public constant STAKING_APY = 25;
    uint256 public architectRewards;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => uint256) public lastSellTimestamp;
    mapping(address => uint256) public soldInWindow;
    uint256 public totalSupply;
    bool public isInitialized;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Burn(address indexed from, uint256 value);
    event LiquidityAdded(uint256 value);

    modifier onlyOwner() { require(isOwner[msg.sender]); _; }
    modifier onlyArchitect() { require(msg.sender == ARCHITECT); _; }

    constructor() {
        ARCHITECT = msg.sender;
        VESTING_START = block.timestamp;
        owners.push(msg.sender);
        isOwner[msg.sender] = true;
        _mint(address(this), TOTAL_SUPPLY);
    }

    function initialize(address _igor, address _team, address _inv, address _dao, address _lp) external onlyArchitect {
        require(!isInitialized); isInitialized = true;
        IGOR = _igor; TEAM_WALLET = _team; INVESTOR_WALLET = _inv; DAO_WALLET = _dao; LIQUIDITY_POOL = _lp;
        _transfer(address(this), _team, TEAM_SHARE);
        _transfer(address(this), _inv, INVESTOR_SHARE);
        _transfer(address(this), _dao, DAO_SHARE);
    }
